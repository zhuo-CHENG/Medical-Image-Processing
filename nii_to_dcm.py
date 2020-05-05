import SimpleITK as sitk

import sys, time, os
import numpy as np

import os
import numpy as np
import SimpleITK as sitk
import argparse


def get_IPP_tag(orig_slice_path):
    reader = sitk.ImageFileReader()
    reader.SetFileName(orig_slice_path)
    reader.LoadPrivateTagsOn();
    reader.ReadImageInformation();

    k = "0020|0032"
    v = reader.GetMetaData(k)
    # print(v)
    slice_IPP = tuple([float(i) for i in v.split('\\')])
    # print(nums)
    return slice_IPP

def writeSlices(writer, series_tag_values, new_img, i):

    depth = new_img.GetDepth()
    image_slice = new_img[:,:,depth-i-1]

    # orig_slice_path = os.path

    # Tags shared by the series.
    list(map(lambda tag_value: image_slice.SetMetaData(tag_value[0], tag_value[1]), series_tag_values))

    # Slice specific tags.
    image_slice.SetMetaData("0008|0012", time.strftime("%Y%m%d")) # Instance Creation Date
    image_slice.SetMetaData("0008|0013", time.strftime("%H%M%S")) # Instance Creation Time

    # Setting the type to CT preserves the slice location.
    image_slice.SetMetaData("0008|0060", "CT")  # set the type to CT so the thickness is carried over

    # (0020, 0032) image position patient determines the 3D spacing between slices.
    # image_slice.SetMetaData("0020|0032", '\\'.join(map(str,new_img.TransformIndexToPhysicalPoint((0,0,depth-i-1))))) # Image Position (Patient)
    image_slice.SetMetaData("0020|0032", '\\'.join(map(str, IPP_list[depth-i-1]))) # Image Position (Patient)

    image_slice.SetMetaData("0020,0013", str(depth-i-1)) # Instance Number

    # Write to the output directory and add the extension dcm, to force writing in DICOM format.
    writer.SetFileName(os.path.join(save_sub_folder,str(i)+'.dcm'))
    writer.Execute(image_slice)


def nii_to_dcm(img_path, img_name):

    img = sitk.ReadImage(img_path)
    data = sitk.GetArrayFromImage(img)
    data = data.astype(np.int8)
    data = np.flip(data,1)
    new_img = sitk.GetImageFromArray(data)
    new_img.CopyInformation(img)
    new_img.SetDirection((1.0,0,0,0,1.0,0,0,0,1.0))
    origin = list(new_img.GetOrigin())
    origin[1] = -origin[1]
    new_img.SetOrigin(tuple(origin))
    writer = sitk.ImageFileWriter()
    # Use the study/series/frame of reference information given in the meta-data
    # dictionary and not the automatically generated information from the file IO
    writer.KeepOriginalImageUIDOn()

    modification_time = time.strftime("%H%M%S")
    modification_date = time.strftime("%Y%m%d")


    # Copy some of the tags and add the relevant tags indicating the change.
    # For the series instance UID (0020|000e), each of the components is a number, cannot start
    # with zero, and separated by a '.' We create a unique series ID using the date and time.
    # tags of interest:
    direction = new_img.GetDirection()

    series_tag_values = [("0008|0031",modification_time), # Series Time
                    ("0008|0021",modification_date), # Series Date
                    ("0008|0008","DERIVED\\SECONDARY"), # Image Type
                    ("0020|000e", "1.2.826.0.1.3680043.2.1125."+modification_date+".1"+modification_time), # Series Instance UID
                    ("0020|0037", '\\'.join(map(str, (direction[0], direction[1], direction[2],# Image Orientation (Patient)
                                                        direction[3],direction[4],direction[5],
                                                        direction[6],direction[7],direction[8])))),
                    ("0008|103e", "Created-SimpleITK")] # Series Description

    # Write slices to output directory
    list(map(lambda i: writeSlices(writer, series_tag_values, new_img, i), range(new_img.GetDepth())))
    


    # ---------- Check the correction ----------

    # # Re-read the series
    # # Read the original series. First obtain the series file names using the
    # # image series reader.
    # data_directory = save_sub_folder
    # series_IDs = sitk.ImageSeriesReader.GetGDCMSeriesIDs(data_directory)
    # if not series_IDs:
    #     print("ERROR: given directory \""+data_directory+"\" does not contain a DICOM series.")
    #     sys.exit(1)
    # series_file_names = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(data_directory, series_IDs[0])

    # series_reader = sitk.ImageSeriesReader()
    # series_reader.SetFileNames(series_file_names)

    # # Configure the reader to load all of the DICOM tags (public+private):
    # # By default tags are not loaded (saves time).
    # # By default if tags are loaded, the private tags are not loaded.
    # # We explicitly configure the reader to load tags, including the
    # # private ones.
    # series_reader.LoadPrivateTagsOn()
    # image3D = series_reader.Execute()
    # print("Spacing:", image3D.GetSpacing(),'vs',new_img.GetSpacing())

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="NIFTI to DICOM")

    parser.add_argument(
        "-n_f",
        "--nii_folder",
        default=None,
        type=str,
        help="The path of NIFTI mask folder",
    )
    parser.add_argument(
        "-d_f",
        "--dcm_folder",
        default=None,
        type=str,
        help="The path of DICOM mask folder",
    )
    parser.add_argument(
        "-o_f",
        "--orig_dcm_folder",
        default=None,
        type=str,
        help="The path of original DICOM image folder",
    )

    args = parser.parse_args()
    img_folder = args.nii_folder
    save_folder = args.dcm_folder
    orig_folder = args.orig_dcm_folder
    if not os.path.exists(save_folder): os.makedirs(save_folder)

    # Get the the path list of files
    files = os.listdir(img_folder)
    img_paths = []
    for file in files:
        if os.path.splitext(file)[-1] == '.gz':
            img_paths.append(os.path.join(img_folder, file))


    # Translation
    for img_path in img_paths:
        img_name = os.path.basename(img_path)
        img_name = img_name.split('.')[0]
        print("Processing: {}".format(img_name))

        save_sub_folder = os.path.join(save_folder, img_name)
        if not os.path.exists(save_sub_folder): os.makedirs(save_sub_folder)

        orig_name = img_name.split('_')[0]
        orig_sub_folder = os.path.join(orig_folder, orig_name)
        orig_slice_filename = os.listdir(orig_sub_folder)
        orig_slice_paths = [os.path.join(orig_sub_folder, filename) for filename in orig_slice_filename]

        IPP_list = []
        for orig_slice_path in orig_slice_paths:
            IPP = get_IPP_tag(orig_slice_path)
            IPP_list.append(IPP)
        # print(IPP_list)
        IPP_list = sorted(IPP_list, key=lambda element: element[2])
        # print(IPP_list)
        nii_to_dcm(img_path, img_name)
        print("------")
