import os
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.metrics import (Accuracy as AccuracyTfKeras, BinaryAccuracy, CategoricalAccuracy,
                                      BinaryCrossentropy as BinaryCrossentropyM,
                                      CategoricalCrossentropy as CategoricalCrossentropyM,
                                      FalsePositives, TruePositives, TrueNegatives, FalseNegatives, Precision, Recall)
from tensorflow.keras.losses import (BinaryCrossentropy as BinaryCrossentropyL,
                                     CategoricalCrossentropy as CategoricalCrossentropyL)
from metrics_utils import (OneHotAccuracyTfKeras, OneHotFalseNegatives, OneHotFalsePositives,
                           OneHotTrueNegatives, OneHotTruePositives, OneHotPrecision, OneHotRecall,
                           ClassBinaryAccuracyTfKeras, OneHotClassBinaryAccuracyTfKeras, ClassBinaryAccuracySM,
                           OneHotClassBinaryAccuracySM, FBetaScore, OneHotFBetaScore, IoUScore, OneHotIoUScore,
                           global_threshold)
os.environ['SM_FRAMEWORK'] = 'tf.keras'  # will tell segmentation models to use tensorflow's keras
from segmentation_models import Unet
from segmentation_models.losses import CategoricalCELoss


def generate_compiled_segmentation_model(model_name, model_parameters, num_classes, loss, optimizer,
                                         weights_to_load=None):

    # These are the only model, loss, and optimizer currently supported
    assert model_name == 'Unet'
    assert loss == 'cross_entropy'
    assert optimizer == 'adam'

    model = Unet(input_shape=(None, None, 1), classes=num_classes, **model_parameters)

    crossentropy = BinaryCrossentropyL()
    loss_fn = crossentropy

    all_metrics = []    # one-hot versions are generally preferred for given metric
    # make first metric a copy of loss, to continually verify `val_loss` is correct
    if isinstance(loss_fn, BinaryCrossentropyL):
        all_metrics.append(BinaryCrossentropyM(name='binary_ce_metric'))
    else:
        all_metrics.append(CategoricalCrossentropyM(name='categ_ce_metric'))

    # standard thresholded version (default threshold is 0.5) also kept below, in case it's desired in certain scenario
    for class_num in range(num_classes + 1):
        if class_num == 0:    # all class metrics
            # note, `loss_fn` for all classes placed before `all_metrics` in lineup of command window metrics and plots
            if not isinstance(loss_fn, BinaryCrossentropyL):
                all_metrics.extend([CategoricalCELoss()])
                all_metrics[1].name = str('categ_cross_entropy_sm')
            all_metrics.extend([
                AccuracyTfKeras(),
                OneHotAccuracyTfKeras(),  # `global_threshold` built-in
                ClassBinaryAccuracyTfKeras(thresholds=global_threshold),
                OneHotClassBinaryAccuracyTfKeras(thresholds=global_threshold),
                ClassBinaryAccuracySM(threshold=global_threshold),
                OneHotClassBinaryAccuracySM(threshold=global_threshold),
                BinaryAccuracy(threshold=global_threshold),
                CategoricalAccuracy(),
                FalseNegatives(name='false_neg', thresholds=global_threshold),
                OneHotFalseNegatives(name='false_neg_1H', thresholds=global_threshold),
                TrueNegatives(name='true_neg', thresholds=global_threshold),
                OneHotTrueNegatives(name='true_neg_1H', thresholds=global_threshold),
                FalsePositives(name='false_pos', thresholds=global_threshold),
                OneHotFalsePositives(name='false_pos_1H', thresholds=global_threshold),
                TruePositives(name='true_pos', thresholds=global_threshold),
                OneHotTruePositives(name='true_pos_1H', thresholds=global_threshold),
                Recall(name='recall', thresholds=global_threshold),
                OneHotRecall(name='recall_1H', thresholds=global_threshold),
                Precision(name='precision', thresholds=global_threshold),
                OneHotPrecision(name='precision_1H', thresholds=global_threshold),
                FBetaScore(name='f1_score', beta=1, thresholds=global_threshold),
                OneHotFBetaScore(name='f1_score_1H', beta=1, thresholds=global_threshold),
                IoUScore(name='iou_score', thresholds=global_threshold),
                OneHotIoUScore(name='iou_score_1H', thresholds=global_threshold)
            ])
        else:    # per class metrics
            all_metrics.append(CategoricalCELoss(class_indexes=class_num - 1))
            all_metrics[-1].name = str('class' + str(class_num - 1) + '_binary_cross_entropy')
            all_metrics.append(ClassBinaryAccuracySM(name=str('class' + str(class_num - 1) + '_binary_accuracy_sm'),
                                                     class_indexes=class_num - 1, threshold=global_threshold))
            all_metrics.append(OneHotClassBinaryAccuracySM(name=str('class' + str(class_num - 1) + '_binary_accuracy_sm_1H'),
                                                           class_indexes=class_num - 1, threshold=global_threshold))
            all_metrics.append(ClassBinaryAccuracyTfKeras(name=str('class' + str(class_num - 1) + '_binary_accuracy_tfkeras'),
                                                          class_id=class_num - 1, thresholds=global_threshold))
            all_metrics.append(OneHotClassBinaryAccuracyTfKeras(name=str('class' + str(class_num - 1) + '_binary_accuracy_tfkeras_1H'),
                                                                class_id=class_num - 1, thresholds=global_threshold))
            all_metrics.append(IoUScore(name=str('class' + str(class_num - 1) + '_iou_score'),
                                        class_id=class_num - 1, thresholds=global_threshold))
            all_metrics.append(OneHotIoUScore(name=str('class' + str(class_num - 1) + '_iou_score_1H'),
                                              class_id=class_num - 1, thresholds=global_threshold))
            all_metrics.append(FBetaScore(name=str('class' + str(class_num - 1) + '_f1_score'),
                                          class_id=class_num - 1,
                                          beta=1, thresholds=global_threshold))
            all_metrics.append(OneHotFBetaScore(name=str('class' + str(class_num - 1) + '_f1_score_1H'),
                                                class_id=class_num - 1,
                                                beta=1, thresholds=global_threshold))
            all_metrics.append(Precision(name=str('class' + str(class_num - 1) + '_precision'),
                                         class_id=class_num - 1, thresholds=global_threshold))
            all_metrics.append(OneHotPrecision(name=str('class' + str(class_num - 1) + '_precision_1H'),
                                               class_id=class_num - 1, thresholds=global_threshold))
            all_metrics.append(Recall(name=str('class' + str(class_num - 1) + '_recall'),
                                      class_id=class_num - 1, thresholds=global_threshold))
            all_metrics.append(OneHotRecall(name=str('class' + str(class_num - 1) + '_recall_1H'),
                                            class_id=class_num - 1, thresholds=global_threshold))

        if num_classes == 1:
            break

    model.compile(optimizer=Adam(),
                  loss=loss_fn,
                  metrics=all_metrics)

    if weights_to_load:
        model.load_weights(weights_to_load)

    return model
