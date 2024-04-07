import cv2
import numpy as np
from osgeo import gdal, osr

class tile_img:
    def __init__(self, img_path:str):
        if not img_path.endswith('tif'):
            raise ValueError("Input image must be in TIFF format.")

        self.img_path = img_path
        self.img = cv2.imread(img_path)
        self.h0, self.w0, _ = self.img.shape

        self.dim = [320*((self.h0//320)+1), 320*((self.w0//320)+1)]
        self.h, self.w = self.dim

    def patchData(self, patch_dim:int, step_size:float, resize:int=None):
        img = cv2.resize(self.img, (self.w//resize, self.h//resize)) if resize else self.img

        ch1 = np.ceil(self.h/patch_dim).astype(int)
        ch2 = np.ceil(self.w/patch_dim).astype(int)

        arr0 = np.zeros((ch1*patch_dim, ch2*patch_dim, 3), dtype=np.uint8)
        arr0[:self.h0, :self.w0] += img
        arr = arr0.astype(np.uint8)

        patch_shape = (patch_dim, patch_dim, 3)
        patches = self.patchify(arr, patch_shape, step=int(patch_dim*step_size))

        img_patches = [patches[i,j,0,:,:,:] for i in range(patches.shape[0]) for j in range(patches.shape[1])]

        return np.array(img_patches), self

    def patchify(self, arr, patch_shape, step):
        patches = []
        for i in range(0, arr.shape[0] - patch_shape[0] + 1, step):
            for j in range(0, arr.shape[1] - patch_shape[1] + 1, step):
                patch = arr[i:i+patch_shape[0], j:j+patch_shape[1]]
                patches.append(patch.reshape((1,) + patch_shape))
        return np.vstack(patches)

    def save_tiff(self, patches, output_path):
        driver = gdal.GetDriverByName("GTiff")
        dataset = driver.Create(output_path, self.w, self.h, 3, gdal.GDT_Byte)

        dataset.SetGeoTransform(self.get_geotransform())
        dataset.SetProjection(self.get_projection())

        for i, patch in enumerate(patches):
            dataset.GetRasterBand(i+1).WriteArray(patch)

        dataset.FlushCache()
        dataset = None

    def get_geotransform(self):
        # Get the geotransform from the original image
        src_ds = gdal.Open(self.img_path)
        geotransform = src_ds.GetGeoTransform()
        src_ds = None
        return geotransform

    def get_projection(self):
        # Get the projection from the original image
        src_ds = gdal.Open(self.img_path)
        projection = src_ds.GetProjection()
        src_ds = None
        return projection
