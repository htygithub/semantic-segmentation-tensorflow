import scipy.io as sio
import numpy as np
import tensorflow as tf
import os
from scipy import misc

IMG_MEAN = np.array((103.939, 116.779, 123.68), dtype=np.float32)
matfn = './utils/color150.mat'

def read_labelcolours(matfn, append_background=False):
    mat = sio.loadmat(matfn)
    color_table = mat['colors']
    shape = color_table.shape

    if append_background:
        color_list = [(255, 255, 255)] + [tuple(color_table[i]) for i in range(shape[0])]
    else:
        color_list = [tuple(color_table[i]) for i in range(shape[0])]

    return color_list

def decode_labels(mask, img_shape, num_classes):
    if num_classes == 151:
        color_table = read_labelcolours(matfn, append_background=True)
    else:
        color_table = read_labelcolours(matfn)
        
    color_mat = tf.constant(color_table, dtype=tf.float32)
    onehot_output = tf.one_hot(mask, depth=num_classes)
    onehot_output = tf.reshape(onehot_output, (-1, num_classes))
    pred = tf.matmul(onehot_output, color_mat)
    pred = tf.reshape(pred, (1, img_shape[0], img_shape[1], 3))
    
    return pred

def prepare_label(input_batch, new_size, num_classes, one_hot=True):
    with tf.name_scope('label_encode'):
        input_batch = tf.image.resize_nearest_neighbor(input_batch, new_size) # as labels are integer numbers, need to use NN interp.
        input_batch = tf.squeeze(input_batch, squeeze_dims=[3]) # reducing the channel dimension.
        if one_hot:
            input_batch = tf.one_hot(input_batch, depth=num_classes)
            
    return input_batch

def load_img(img_path):
    if os.path.isfile(img_path):
        print('successful load img: {0}'.format(img_path))
    else:
        print('not found file: {0}'.format(img_path))
        sys.exit(0)

    filename = img_path.split('/')[-1]
    img = misc.imread(img_path, mode='RGB')

    return img, filename

def preprocess(img, input_size, model):
    # Convert RGB to BGR
    img_r, img_g, img_b = tf.split(axis=2, num_or_size_splits=3, value=img)
    img = tf.cast(tf.concat(axis=2, values=[img_b, img_g, img_r]), dtype=tf.float32)
        
    # Extract mean.
    img -= IMG_MEAN

    if model == 'fcn-8s':
        shape = tf.shape(img)
        img = tf.expand_dims(img, dim=0)
        output = tf.image.resize_bilinear(img, input_size)

        return output, shape
    elif model == 'pspnet50':
        shape = tf.shape(img)
        h, w = (tf.maximum(input_size[0], shape[0]), tf.maximum(input_size[1], shape[1]))
        pad_img = tf.image.pad_to_bounding_box(img, 0, 0, h, w)
        output = tf.expand_dims(pad_img, dim=0)
       
        return output, h, w, shape


