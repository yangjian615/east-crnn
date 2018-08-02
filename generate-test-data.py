import argparse
import os.path as ops
import os
import numpy as np
import cv2
import tensorflow as tf
import sys

from local_utils import establish_char_dict

char_dict_path=ops.join(os.getcwd(), 'data/char_dict/char_dict.json')
ord_map_dict_path=ops.join(os.getcwd(), 'data/char_dict/ord_map.json')
__char_list = establish_char_dict.CharDictBuilder.read_char_dict(char_dict_path)
__ord_map = establish_char_dict.CharDictBuilder.read_ord_map_dict(ord_map_dict_path)\


def char_list(self):
    """

    :return:
    """
    return self.__char_list


def int64_feature(value):
    """
        Wrapper for inserting int64 features into Example proto.
    """
    if not isinstance(value, list):
        value = [value]
    value_tmp = []
    is_int = True
    for val in value:
        if not isinstance(val, int):
            is_int = False
            value_tmp.append(int(float(val)))
    if is_int is False:
        value = value_tmp
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def float_feature(value):
    """
        Wrapper for inserting float features into Example proto.
    """
    if not isinstance(value, list):
        value = [value]
    value_tmp = []
    is_float = True
    for val in value:
        if not isinstance(val, int):
            is_float = False
            value_tmp.append(float(val))
    if is_float is False:
        value = value_tmp
    return tf.train.Feature(float_list=tf.train.FloatList(value=value))


def bytes_feature(value):
    """
        Wrapper for inserting bytes features into Example proto.
    """
    if not isinstance(value, bytes):
        if not isinstance(value, list):
            value = value.encode('utf-8')
        else:
            value = [val.encode('utf-8') for val in value]
    if not isinstance(value, list):
        value = [value]
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))


def char_to_int(self, char):
    """

    :param char:
    :return:
    """
    temp = ord(char)
    # convert upper character into lower character
    if 65 <= temp <= 90:
        temp = temp + 32

    for k, v in self.__ord_map.items():
        if v == str(temp):
            temp = int(k)
            return temp
    raise KeyError("Character {} missing in ord_map.json".format(char))

    # TODO
    # Here implement a double way dict or two dict to quickly map ord and it's corresponding index


def int_to_char(self, number):
    """

    :param number:
    :return:
    """
    if number == '1':
        return '*'
    if number == 1:
        return '*'
    else:
        return self.__char_list[str(number)]


def encode_labels(self, labels):
    """
        encode the labels for ctc loss
    :param labels:
    :return:
    """
    encoded_labeles = []
    lengths = []
    for label in labels:
        encode_label = [self.char_to_int(char) for char in label]
        encoded_labeles.append(encode_label)
        lengths.append(len(label))
    return encoded_labeles, lengths


def sparse_tensor_to_str(self, spares_tensor: tf.SparseTensor):
    """
    :param spares_tensor:
    :return: a str
    """
    indices = spares_tensor.indices
    values = spares_tensor.values
    values = np.array([self.__ord_map[str(tmp)] for tmp in values])
    dense_shape = spares_tensor.dense_shape

    number_lists = np.ones(dense_shape, dtype=values.dtype)
    str_lists = []
    res = []
    for i, index in enumerate(indices):
        number_lists[index[0], index[1]] = values[i]
    for number_list in number_lists:
        str_lists.append([self.int_to_char(val) for val in number_list])
    for str_list in str_lists:
        res.append(''.join(c for c in str_list if c != '*'))
    return res


#
#
#
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=str)
    parser.add_argument('--out', type=str)
    args = parser.parse_args()
    modes = ['train', 'test', 'val']

    with open(ops.join(args.root, 'lexicon.txt'), 'r') as lex_file:
        dictionary = np.array([tmp.strip().split() for tmp in lex_file.readlines()])

    for mode in modes:
        test_tfrecord_path = ops.join(args.out, '{}_features.tfrecords'.format(mode))
        loadandexport(args.root, 'annotation_{}.txt'.format(mode), test_tfrecord_path, dictionary)


#
#
#
def loadandexport(root, name, out, dictionary):
    with open(ops.join(root, name), 'r') as data, tf.python_io.TFRecordWriter(out) as writer:
        info = np.array([tmp.strip().split() for tmp in data.readlines()])
        index = 0
        for entry in info:
            index = index + 1
            image = cv2.imread(ops.join(root, entry[0]), cv2.IMREAD_COLOR)
            if image is not None:
                image_org = cv2.resize(image, (100, 32))
                filename = ops.basename(entry[0])
                features = tf.train.Features(feature={
                    'labels': int64_feature(int(entry[1])),
                    'images': bytes_feature(bytes(list(np.reshape(image_org, [100 * 32 * 3])))),
                    'imagenames': bytes_feature(filename)
                })
                example = tf.train.Example(features=features)
                writer.write(example.SerializeToString())
            sys.stdout.write('\r>>Writing {:d}/{:d} {:s} tfrecords'.format(index + 1, len(info), filename))
            sys.stdout.flush()
        sys.stdout.write('\n')
        sys.stdout.flush()


if __name__ == '__main__':
    main()