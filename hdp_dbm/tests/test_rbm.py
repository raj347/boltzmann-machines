import os
from shutil import rmtree
from numpy.testing import (assert_allclose,
                           assert_almost_equal)

import env
from utils.rng import RNG
from rbm import BernoulliRBM, MultinomialRBM, GaussianRBM


class TestRBM(object):
    def __init__(self):
        self.X = RNG(seed=1337).rand(32, 24)
        self.X_val = RNG(seed=42).rand(16, 24)
        self.rbm_config = dict(n_visible=24,
                               n_hidden=16,
                               verbose=False,
                               random_seed=1337,
                               sample_h_states=False,
                               L2=0.)

    def cleanup(self):
        for d in ('test_rbm_1/', 'test_rbm_2/', 'test_rbm_3/'):
            if os.path.exists(d):
                rmtree(d)

    def test_fit_consistency(self):
        for C in (BernoulliRBM, MultinomialRBM, GaussianRBM):
            for dtype in ('float32', 'float64'):
                # 1) train 2, then 5 more epochs
                rbm = C(max_epoch=2,
                        model_path='test_rbm_1/',
                        tf_dtype=dtype,
                        **self.rbm_config)

                if dtype == 'float32': assert_almost_equal(rbm.get_tf_params(scope='weights')['W'][0][0], -0.0094548017)
                if dtype == 'float64': assert_almost_equal(rbm.get_tf_params(scope='weights')['W'][0][0], -0.0077341544416)
                rbm.fit(self.X)
                rbm_weights = rbm.set_params(max_epoch=7) \
                    .fit(self.X) \
                    .get_tf_params(scope='weights')

                # 2) train 2 (+save), load and train 5 more epochs
                rbm2 = C(max_epoch=2,
                         model_path='test_rbm_2/',
                         tf_dtype=dtype,
                         **self.rbm_config)
                rbm2.fit(self.X)
                rbm2_weights = C.load_model('test_rbm_2/') \
                    .set_params(max_epoch=7) \
                    .fit(self.X) \
                    .get_tf_params(scope='weights')
                assert_allclose(rbm_weights['W'], rbm2_weights['W'])
                assert_allclose(rbm_weights['hb'], rbm2_weights['hb'])
                assert_allclose(rbm_weights['vb'], rbm2_weights['vb'])

                # train 7 epochs
                rbm3 = C(max_epoch=7,
                         model_path='test_rbm_3/',
                         tf_dtype=dtype,
                         **self.rbm_config)
                rbm3_weights = rbm3.fit(self.X) \
                    .get_tf_params(scope='weights')
                assert_allclose(rbm2_weights['W'], rbm3_weights['W'])
                assert_allclose(rbm2_weights['hb'], rbm3_weights['hb'])
                assert_allclose(rbm2_weights['vb'], rbm3_weights['vb'])

                # cleanup
                self.cleanup()


    def test_fit_consistency_val(self):
        for C in (BernoulliRBM,):

            # 1) train 2, then 5 more epochs
            rbm = C(max_epoch=2,
                    model_path='test_rbm_1/',
                    **self.rbm_config)

            rbm.fit(self.X, self.X_val)
            rbm_weights = rbm.set_params(max_epoch=7) \
                .fit(self.X, self.X_val) \
                .get_tf_params(scope='weights')

            # 2) train 2 (+save), load and train 5 more epochs
            rbm2 = C(max_epoch=2,
                     model_path='test_rbm_2/',
                     **self.rbm_config)
            rbm2.fit(self.X, self.X_val)
            rbm2_weights = C.load_model('test_rbm_2/') \
                .set_params(max_epoch=7) \
                .fit(self.X, self.X_val) \
                .get_tf_params(scope='weights')
            assert_allclose(rbm_weights['W'], rbm2_weights['W'])
            assert_allclose(rbm_weights['hb'], rbm2_weights['hb'])
            assert_allclose(rbm_weights['vb'], rbm2_weights['vb'])

            # train 7 epochs
            rbm3 = C(max_epoch=7,
                     model_path='test_rbm_3/',
                     **self.rbm_config)
            rbm3_weights = rbm3.fit(self.X, self.X_val) \
                .get_tf_params(scope='weights')
            assert_allclose(rbm2_weights['W'], rbm3_weights['W'])
            assert_allclose(rbm2_weights['hb'], rbm3_weights['hb'])
            assert_allclose(rbm2_weights['vb'], rbm3_weights['vb'])

            # cleanup
            self.cleanup()

    def test_transform(self):
        for C in (BernoulliRBM, MultinomialRBM, GaussianRBM):
            rbm = C(max_epoch=2,
                    model_path='test_rbm_1/',
                    **self.rbm_config)
            rbm.fit(self.X)
            H = rbm.transform(self.X_val)

            H_loaded = C.load_model('test_rbm_1/').transform(self.X_val)
            assert H.shape == (len(self.X_val), 16)
            assert_allclose(H, H_loaded)

            # cleanup
            self.cleanup()

    def tearDown(self):
        self.cleanup()
