import sys
# TODO : command line utility to supersede the GUI
# kinda done, just needs a parser really
import torch
from torch.utils.data import DataLoader, TensorDataset
from torchvision.datasets import MNIST
from torchvision import transforms
from training import TrainingManager

from metrics import FID

dset_path = sys.argv[1]

def test_FID_MNIST(load=True):
    premade = MNIST("./mnist/", train=True, transform = transforms.Compose([
        transforms.Resize(32),
        transforms.ToTensor(),
        transforms.Normalize(0.5, 0.5),
    ]), download=True)

    tr_3c = transforms.Lambda(lambda x: x.expand(3, -1, -1))

    premade_3 = MNIST("./mnist/", train=True, transform = transforms.Compose([
        transforms.Resize(32),
        transforms.ToTensor(),
        tr_3c,
        transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5]),
    ]), download=True)

    manager = TrainingManager(debug=True)
    params = {
        "arch": "DCGAN_EZMNIST",
        "img_size": 32,
        "batch_size": 256,
        "latent_size": 100,
        "learning_rate": 0.0002,
        "b1": 0.5,
        "b2": 0.999,
    }
    if load:
        manager.load("./savestates/DCGAN_EZMNIST_20220507174350_5.pth", premade=premade)
    else:
        manager.set_trainer(params, premade=premade)



    # grab 1000 real images, replicating their channel for RGB
    reals = DataLoader(premade_3, 1000, shuffle=True)
    reals = next(iter(reals))[0] # for datasets with labels : only grab the actual data
    reals = DataLoader(reals, 32, shuffle=True)

    # grab 1000 fake images, replicating their channel for RGB
    fakes = torch.randn(1000, 100, 1, 1)
    with torch.no_grad():
        fakes = manager.trainer.GEN(fakes)
    fakes = fakes.expand(-1, 3, -1, -1)
    fakes = DataLoader(fakes, 32, shuffle=True)

    print(FID(reals, fakes, 32, 2048, 'cpu'))

    #  to make it work :
    # prepare a dataloader of your N samples from each set
    # just give em to fid
    # ???
    # profit

def test_sagan():

    img_folder = dset_path
    params = {
        "arch": "SAGAN_TEST_WGP",
        "img_size": 32,
        "batch_size": 16,
        "latent_size": 100,
        "learning_rate": 0.0002,
        "b1": 0.5,
        "b2": 0.999,
        "critic_iters": 5,
        "lambda_gp": 10,
    }
    manager = TrainingManager(debug=True)
    manager.set_dataset_folder(img_folder)
    manager.set_trainer(params)
    return manager

def test_dcgan():

    img_folder = dset_path
    params = {
        "arch": "DCGAN",
        "grids_g": [1, 4, 8, 16, 32],
        "grids_d": [32, 16, 8, 4, 1],
        "img_size": 32,
        "batch_size": 16,
        "latent_size": 100,
        "learning_rate": 0.0002,
        "b1": 0.5,
        "b2": 0.999,
    }
    manager = TrainingManager(debug=True)
    manager.set_dataset_folder(img_folder)
    manager.set_trainer(params)
    return manager

def test_wgangp():
    
    img_folder = dset_path
    params = {
        "arch": "WGAN_GP",
        "grids_g": [1, 4, 8, 16, 32],
        "grids_d": [32, 16, 8, 4, 1],
        "img_size": 32,
        "batch_size": 16,
        "latent_size": 100,
        "learning_rate": 0.0002,
        "b1": 0.5,
        "b2": 0.999,
        "critic_iters": 5,
        "lambda_gp": 10,
    }
    manager = TrainingManager(debug=True)
    manager.set_dataset_folder(img_folder)
    manager.set_trainer(params)
    return manager
