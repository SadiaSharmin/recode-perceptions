from pathlib import Path
from timeit import default_timer as timer

import torch
import torch.nn as nn

from . import train
from .dataset_generator import dataloader
from .logger import logger
from .model_builder import MyCNN
from .utils import detect_device, output_plots

# import wandb
# logging config
# logger.logger()


def main(opt):

    # log output
    logger.info("Model running with parameters: %s" % opt)

    # detect devices
    device = detect_device()

    # WANDB for HO
    # id = '%s' % opt.wandb_name
    # wandb.login(key='')
    # wandb.init(id = id, project='place_pulse_phd', entity='emilymuller1991')

    # create dataloaders
    params = {
        "batch_size": opt.batch_size,
        "shuffle": True,
        "num_workers": 1,
        "pin_memory": True,
        "drop_last": False,
    }
    train_dataloader, N = dataloader(
        opt.data_dir, opt.root_dir, opt.pre, "train", params
    )
    validation_dataloader, _ = dataloader(
        opt.data_dir, opt.root_dir, opt.pre, "val", params
    )
    test_dataloader, _ = dataloader(opt.data_dir, opt.root_dir, opt.pre, "test", params)

    # initialise model
    model = MyCNN(n_classes=N)
    model.to(device)
    logger.info("Model loaded with %s parameters" % str(model.count_params()))

    # Set up Loss and Optimizer
    optimizer = torch.optim.Adam(model.parameters(), opt.lr)

    def lambda_decay(epoch):
        # defines learning rate decay
        return opt.lr * 1 / (1.0 + (opt.lr / opt.epochs) * epoch)

    scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda_decay)
    loss_fn = nn.CrossEntropyLoss()

    # Start the timer
    start_time = timer()

    # Train model
    train_val_loss = train.train(
        model=model,
        train_dataloader=train_dataloader,
        val_dataloader=validation_dataloader,
        optimizer=optimizer,
        scheduler=scheduler,
        loss_fn=loss_fn,
        epochs=opt.epochs,
        device=device,
        save_model=Path(opt.root_dir, "outputs/models/", opt.run_name + ".pt"),
        wandb=False,
    )
    output_plots(train_val_loss, opt.root_dir, opt.run_name)

    # End the timer and logger.info out how long it took
    end_time = timer()
    logger.info(f"Model trained in: {end_time-start_time:.3f} seconds")

    # Get Test Performance
    test_loss = train.test_step(
        model=model,
        test_dataloader=test_dataloader,
        loss_fn=loss_fn,
        device=device,
    )
    logger.info(f"Model tested in: {timer()-end_time:.3f} seconds")

    logger.info(
        "LOSS train {} valid {} test {}".format(
            train_val_loss["train_loss"][-1], train_val_loss["val_loss"][-1], test_loss
        )
    )


# PLOTS
# plot training loss
# plot validation loss
# plot test prediction histogram


# y[i] = np.squeeze(toutputs.cpu().detach().numpy())
# y_true[i] = np.squeeze(tlabels.numpy())
# y = y[y != 0]
# y_true = y_true[y_true != 0]
# avg_testloss = running_tloss/(i+1)
# prediction_hist(y.flatten(), y_true.flatten(), opt.model + '
# _epochs_' + str(opt.epochs) + '_lr_' + str(opt.lr)  + str(opt.oversample)
#  + str(opt.study_id), opt.prefix )
# logger.info('LOSS train {} valid {} test {}'
# .format(avg_tloss, avg_vloss, avg_testloss))
