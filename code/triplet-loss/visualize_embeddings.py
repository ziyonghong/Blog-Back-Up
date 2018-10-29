# -*- coding: utf-8 -*-
# Author: Lawlite
# Date: 2018/10/20
# Associate Blog: http://lawlite.me/2018/10/16/Triplet-Loss原理及其实现/#more
# License: MIT

import os
import numpy as np
import tensorflow as tf
import argparse
from triplet_loss import batch_all_triplet_loss
from triplet_loss import batch_hard_triplet_loss
import mnist_dataset
from train_with_triplet_loss import my_model
from train_with_triplet_loss import test_input_fn
from tensorflow.contrib.tensorboard.plugins import projector

parser = argparse.ArgumentParser()
parser.add_argument('--data_dir', default='data',type=str, help="数据地址")
parser.add_argument('--model_dir', default='experiment/model', type=str, help="模型地址")
parser.add_argument('--sprite_filename', default='experiments/mnist_10k_sprite.png',
                    help="Sprite image for the projector")

def main(argv):
    args = parser.parse_args(argv[1:])
    params = {
        "learning_rate": 1e-3,
        "batch_size": 64,
        "num_epochs": 20,
    
        "num_channels": 32,
        "use_batch_norm": False,
        "bn_momentum": 0.9,
        "margin": 0.5,
        "embedding_size": 64,
        "triplet_strategy": "batch_hard",
        "squared": False,
    
        "image_size": 28,
        "num_labels": 10,
        "train_size": 50000,
        "eval_size": 1000,
    
        "num_parallel_calls": 4        
    }
    tf.logging.info("创建模型....")
    config = tf.estimator.RunConfig(model_dir=args.model_dir, tf_random_seed=100)  # config
    cls = tf.estimator.Estimator(model_fn=my_model, config=config, params=params)  # 建立模型
    
    tf.logging.info("预测....")
    
    predictions = cls.predict(input_fn=lambda: test_input_fn(args.data_dir, params))
    embeddings = np.zeros((params['eval_size'], params['embedding_size']))
    for i, p in enumerate(predictions):
        if i>=params['eval_size']:
            break
        embeddings[i] = p['embeddings']
    tf.logging.info("embeddings shape: {}".format(embeddings.shape))
    
    with tf.Session() as sess:
        # Obtain the test labels
        dataset = mnist_dataset.test(args.data_dir)
        dataset = dataset.map(lambda img, lab: lab)
        dataset = dataset.batch(params['eval_size'])
        labels_tensor = dataset.make_one_shot_iterator().get_next()
        labels = sess.run(labels_tensor)    
    np.savetxt(os.path.join(args.model_dir, 'metadata.tsv'), labels, fmt='%d')
    
    with tf.Session() as sess:
        embedding_var = tf.Variable(embeddings, name="mnist_embeddings")
        tf.global_variables_initializer().run()
        
        saver = tf.train.Saver([embedding_var])
        sess.run(embedding_var.initializer)
        saver.save(sess, os.path.join(args.model_dir, 'embeddings.ckpt'), global_step=0)
        
        summary_writer = tf.summary.FileWriter(args.model_dir)
        config = projector.ProjectorConfig()
        embedding = config.embeddings.add()
        embedding.tensor_name = embeddings_var.name
        embedding.metadata_path = 'mnist_10k_sprite.png'
        embedding.sprite.image_path = 'metadata.tsv'
        embedding.sprite.single_image_dim.extend([28, 28])
        projector.visualize_embeddings(summary_writer, config)


if __name__ == '__main__':
    tf.app.run(main)
        