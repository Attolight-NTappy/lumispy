# -*- coding: utf-8 -*-
# Copyright 2019 The LumiSpy developers
#
# This file is part of LumiSpy.
#
# LumiSpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# LumiSpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with LumiSpy.  If not, see <http://www.gnu.org/licenses/>.

# a lot of stuff depends on this, so we have to create it first

import glob
import logging
import os
import warnings
import numpy as np

#from hyperspy.io import load as hyperspyload
#from hyperspy.io import load_with_reader

from hyperspy.signals import Signal2D
from lumispy.signals.cl_sem import CLSEMSpectrum

from .acquisition_systems import acquisition_systems




def load_hypcard(hypcard_file, lazy = False, acquisition_system
                 = 'cambridge_attolight'):
    """Load data into pyxem objects.
    Parameters
    ----------
    hypcard_file : str
        The HYPCard.bin file for the file to be loaded, created by AttoLight
        software. Please, state the directory.
    lazy : bool
        If True the file will be opened lazily, i.e. without actually reading
        the data from the disk until required. Allows datasets much larger than
        available memory to be loaded.
    metadata_file_name: str
        By default, AttoLight software names it 'MicroscopeStatus.txt'.
        Otherwise, specify.
    acquisition_system : str
        Specify which acquisition system the HYPCard was taken with, from the
        acquisition_systems.py dictionary file. By default, it assumes it is
        the Cambridge Attolight SEM system.
    Returns
    -------
    s : Signal
        A pyxem Signal object containing loaded data.
    """
    def get_metadata(hypcard_folder, metadata_file_name):
        """Import the metadata from the MicroscopeStatus.txt file.
        Returns binning, nx, ny, FOV, grating and central_wavelength.
        Parameters
        ----------
        hypcard_folder : str
            The absolute folder path where the metadata_file_name exists.
        """
        path = os.path.join(hypcard_folder, metadata_file_name)
        with open(path, encoding='windows-1252' ) as status:
            for line in status:
                if 'Horizontal Binning:' in line:
                    binning = int(line[line.find(':')+1:-1])        #binning = binning status
                if 'Resolution_X' in line:
                    nx = int(line[line.find(':')+1:-7])
                    #nx = pixel in x-direction
                if 'Resolution_Y' in line:
                    ny = int(line[line.find(':')+1:-7])
                    #ny = pixel in y-direction
                if 'Real Magnification' in line:
                     FOV = float(line[line.find(':')+1:-1])
                if 'Grating - Groove Density:' in line:
                    grating = float(line[line.find(':')+1:-6])
                if 'Central wavelength:' in line:
                    central_wavelength_nm = float(line[line.find(':')+1:-4])
                if 'Channels:' in line:
                    total_channels = int(line[line.find(':')+1:-1])
                if 'Signal Amplification:' in line:
                    amplification = int(line[line.find(':x')+2:-1])
                if 'Readout Rate (horizontal pixel shift):' in line:
                    readout_rate_hz = int(line[line.find(':')+1:-4])

                if 'Exposure Time:' in line:
                    exposure_time_ccd_s = float(line[line.find(':')+1:-3])
                if 'HYP Dwelltime:' in line:
                    dwell_time_scan_s = float(line[line.find(':')+1:-4])/1000
                if 'Beam Energy:' in line:
                    beam_acc_voltage_kv = float(line[line.find(':')+1:-3])/1000
                if 'Gun Lens:' in line:
                    gun_lens_amps = float(line[line.find(':')+1:-3])
                if 'Objective Lens:' in line:
                    obj_lens_amps = float(line[line.find(':')+1:-3])
                if 'Aperture:' in line:
                    aperture_um = float(line[line.find(':')+1:-4])
                if 'Aperture Chamber Pressure:' in line:
                    chamber_pressure_torr = float(line[line.find(':')+1:-6])

        # Correct channels to the actual value, accounting for binning. Get
        # channels on the detector used (if channels not defined, then assume
        # its 1024)
        try:
            total_channels
        except:
            total_channels = acquisition_systems[acquisition_system]['channels']
        channels =  total_channels//binning

        #Return metadata
        return binning, nx, ny, FOV, grating, central_wavelength_nm, channels, amplification, readout_rate_hz, exposure_time_ccd_s,  dwell_time_scan_s, beam_acc_voltage_kv, gun_lens_amps, obj_lens_amps, aperture_um, chamber_pressure_torr

    def store_metadata(cl_object, hypcard_folder, metadata_file_name,
                       acquisition_system):
        """
        TO BE ADDED
        Store metadata in the CLSpectrum object metadata property. Stores
        binning, nx, ny, FOV, grating and central_wavelength.
        Parameters
        ----------
        cl_object: CLSpectrum object
            The CLSpectrum object where to save the metadata.
        hypcard_folder : str
            The absolute folder path where the metadata_file_name exists.
        """
        #Get metadata
        binning, nx, ny, FOV, grating, central_wavelength_nm, channels, amplification, readout_rate_hz, exposure_time_ccd_s, dwell_time_scan_s, beam_acc_voltage_kv, gun_lens_amps, obj_lens_amps, aperture_um, chamber_pressure_torr = get_metadata(hypcard_folder, metadata_file_name)

        #Store metadata
        cl_object.metadata.set_item("Acquisition_instrument.Spectrometer.grating",
                                    grating)
        cl_object.metadata.set_item("Acquisition_instrument.Spectrometer.central_wavelength_nm",
                                    central_wavelength_nm)
        cl_object.metadata.set_item("Acquisition_instrument.SEM.resolution_x",
                                    nx)
        cl_object.metadata.set_item("Acquisition_instrument.SEM.resolution_y",
                                    ny)
        cl_object.metadata.set_item("Acquisition_instrument.SEM.FOV", FOV)
        cl_object.metadata.set_item("Acquisition_instrument.CCD.binning",
                                    binning)
        cl_object.metadata.set_item("Acquisition_instrument.CCD.channels",
                                    channels)
        cl_object.metadata.set_item("Acquisition_instrument.acquisition_system",
                                    acquisition_system)
        cl_object.metadata.set_item("Acquisition_instrument.CCD.amplification",amplification)
        cl_object.metadata.set_item("Acquisition_instrument.CCD.readout_rate_hz", readout_rate_hz)
        cl_object.metadata.set_item("Acquisition_instrument.CCD.exposure_time_s", exposure_time_ccd_s)
        cl_object.metadata.set_item("Acquisition_instrument.SEM.dwell_time_scan_s", dwell_time_scan_s)
        cl_object.metadata.set_item("Acquisition_instrument.SEM.beam_acc_voltage_kv", beam_acc_voltage_kv)
        cl_object.metadata.set_item("Acquisition_instrument.SEM.gun_lens_amps", gun_lens_amps)
        cl_object.metadata.set_item("Acquisition_instrument.SEM.obj_lens_amps", obj_lens_amps)
        cl_object.metadata.set_item("Acquisition_instrument.SEM.aperture_um", aperture_um)
        cl_object.metadata.set_item("Acquisition_instrument.SEM.chamber_pressure_torr", chamber_pressure_torr)

        return cl_object

    def calibrate_signal_axis_wavelength(cl_object):
        """
        Based on the Attolight software export function. Need to be automatised.
        Two calibrated sets show the trend:
        #Centre at 650 nm:
            spec_start= 377.436, spec_end = 925.122
        #Centre at 750:
            spec_start= 478.2, spec_end = 1024.2472
        Returns
        ----------
        spectra_offset_array: []
            Array containing the spectrum energy axis start and end points in
            nm (from the MeanSpectrum file), such as [spec_start, spec_end]
        """
        #Get relevant parameters from metadata
        central_wavelength = cl_object.metadata.Acquisition_instrument.Spectrometer.central_wavelength_nm

        #Estimate start and end wavelengths
        spectra_offset_array = [central_wavelength-273, central_wavelength+273]

        #Apply calibration
        dx = cl_object.axes_manager.signal_axes[0]
        dx.name = 'Wavelength'
        dx.scale = (spectra_offset_array[1] - spectra_offset_array[0]) \
                                / cl_object.axes_manager.signal_size
        dx.offset = spectra_offset_array[0]
        dx.units = '$nm$'

        return cl_object

    def calibrate_navigation_axis(cl_object):
        # Edit the navigation axes
        x = cl_object.axes_manager.navigation_axes[0]
        y = cl_object.axes_manager.navigation_axes[1]

        # Get relevant parameters from metadata and acquisition_systems
        # parameters
        acquisition_system \
            = cl_object.metadata.Acquisition_instrument.acquisition_system
        cal_factor_x_axis \
            = acquisition_systems[acquisition_system]['cal_factor_x_axis']
        FOV = cl_object.metadata.Acquisition_instrument.SEM.FOV
        nx = cl_object.metadata.Acquisition_instrument.SEM.resolution_x

        # Get the calibrated scanning axis scale from the acquisition_systems
        # dictionary
        calax = cal_factor_x_axis/(FOV*nx)
        x.name = 'x'
        x.scale = calax * 1000
        #changes micrometer to nm, value for the size of 1 pixel
        x.units = 'nm'
        y.name = 'y'
        y.scale = calax * 1000
        #changes micrometer to nm, value for the size of 1 pixel
        y.units = 'nm'

        return cl_object

    def save_background(cl_object, hypcard_folder, background_file_name='Background*.txt'):
        """
        Based on the Attolight background savefunction.
        If background is found in the folder, it saves background as a cl_object.background attribute.

        Returns
        ----------
        cl_object:
            With the background saved as a background attribute.
        """
        #Get the absolute path
        path = os.path.join(hypcard_folder, background_file_name)
        #Try to load the file, if it exists.
        try:
            #Find the exact filename, using the * wildcard
            path = glob.glob(path)
            #Load the file as a numpy array
            bkg = np.loadtxt(path)
            #Extract only the  signal axis
            #ERROR from AttoLight bug
            bkg = bkg[1]
            #Retrieve the correct x axis from the cl_object
            #ERROR from AttoLight bug
            x_axis = cl_object.axes_manager.signal_axes[0].axis
            #Join x axis with bkg signal
            background = [x_axis, bkg]
            #Store the value as background attribute
            cl_object.background = background
            return cl_object

        #If file does not exist, return function
        except:
            return


    #################################

    #Loading function starts here
    #Import folder name
    hypcard_folder = os.path.split(os.path.abspath(hypcard_file))[0]

    #Import metadata
    metadata_file_name \
                = acquisition_systems[acquisition_system]['metadata_file_name']

    binning, nx, ny, FOV, grating, central_wavelength_nm, channels, amplification, readout_rate_hz, exposure_time_ccd_s, dwell_time_scan_s, beam_acc_voltage_kv, gun_lens_amps, obj_lens_amps, aperture_um, chamber_pressure_torr = get_metadata(hypcard_folder, metadata_file_name)


    #Load file
    with open(hypcard_file, 'rb') as f:
        data = np.fromfile(f, dtype= [('bar', '<i4')], count= channels*nx*ny)
        array = np.reshape(data, [channels, nx, ny], order='F')

    #Swap x-y axes to get the right xy orientation
    sarray = np.swapaxes(array, 1,2)

    ##Make the CLSEMSpectrum object
    #Load the transposed data
    s = Signal2D(sarray).T
    s.change_dtype('float')
    s = CLSEMSpectrum(s)

    #Add all parameters as metadata
    store_metadata(s, hypcard_folder, metadata_file_name, acquisition_system)

    ##Add name as metadata
    if acquisition_system == 'cambridge_attolight':
        #Import file name
        experiment_name = os.path.split(hypcard_folder)[1]
        #CAUTION: Specifically delimeted by Attolight default naming system
        try:
            name = experiment_name[:-37]
        except:
            name = experiment_name
        s.metadata.General.title = name

    #Save background file if exisent
    save_background(s, hypcard_folder)

    #Calibrate navigation axis
    calibrate_navigation_axis(s)

    #Calibrate signal axis
    calibrate_signal_axis_wavelength(s)


    return(s)
