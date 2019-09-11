import numpy as np
import tensorflow as tf
import tensorflow_probability as tfp

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

initializer_helper = {
    'kernel_initializer': tf.truncated_normal_initializer(0, .1),
    'bias_initializer': tf.constant_initializer(.1)
}


class SAC_Custom(object):
    def _build_lstm_s_input(self, s_input, scope, trainable=True, reuse=False):
        with tf.variable_scope(scope, reuse=reuse):
            is_input_2_dim = len(s_input.shape) == 2
            if is_input_2_dim:
                s_input = tf.reshape(s_input, (-1, 1, self.s_dim))

            lstm_cell = tf.nn.rnn_cell.BasicLSTMCell(2, trainable=trainable)
            initial_lstm_state = lstm_cell.zero_state(self.pl_batch_size, dtype=tf.float32)
            l, lstm_state = tf.nn.dynamic_rnn(lstm_cell,
                                              inputs=s_input,
                                              initial_state=initial_lstm_state,
                                              dtype=tf.float32)

            # l = tf.layers.dense(l, 2, activation=tf.nn.tanh, trainable=trainable, **initializer_helper)

            if is_input_2_dim:
                encoded_s = tf.reshape(l, (-1, l.shape[2]))
            else:
                encoded_s = l

            variables = tf.get_variable_scope().global_variables()

        return encoded_s, initial_lstm_state, lstm_state, variables
        
    def _build_q_net(self, s_input, a_input, scope, trainable=True, reuse=False):
        with tf.variable_scope(scope, reuse=reuse):
            ls = tf.layers.dense(
                s_input, 32, activation=tf.nn.tanh,
                trainable=trainable, **initializer_helper
            )
            la = tf.layers.dense(
                a_input, 32, activation=tf.nn.tanh,
                trainable=trainable, **initializer_helper
            )
            l = tf.concat([ls, la], 1)
            l = tf.layers.dense(l, 32, activation=tf.nn.relu, trainable=trainable, **initializer_helper)
            l = tf.layers.dense(l, 32, activation=tf.nn.relu, trainable=trainable, **initializer_helper)
            q = tf.layers.dense(l, 1, **initializer_helper, trainable=trainable)

            variables = tf.get_variable_scope().global_variables()

        return q, variables

    def _build_policy_net(self, s_inputs, scope, trainable=True, reuse=False):
        with tf.variable_scope(scope, reuse=reuse):
            l = tf.layers.dense(s_inputs, 32, tf.nn.relu, **initializer_helper, trainable=trainable)
            l = tf.layers.dense(l, 32, tf.nn.relu, **initializer_helper, trainable=trainable)

            mu = tf.layers.dense(l, 32, tf.nn.relu, **initializer_helper, trainable=trainable)
            mu = tf.layers.dense(mu, self.a_dim, tf.nn.tanh, **initializer_helper, trainable=trainable)

            sigma = tf.layers.dense(l, 32, tf.nn.relu, **initializer_helper, trainable=trainable)
            sigma = tf.layers.dense(sigma, self.a_dim, tf.nn.sigmoid, **initializer_helper, trainable=trainable)
            sigma = sigma + .1

            policy = tfp.distributions.Normal(loc=mu, scale=sigma)
            action = policy.sample()

            variables = tf.get_variable_scope().global_variables()

        return policy, action, variables