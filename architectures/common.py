import datetime
import torch
from torch.utils import data
import torchvision.datasets as dset
import torchvision.transforms as transforms
import torchvision.utils as vutils
from . import DCGANTrainer, WGAN_GPTrainer

#TODO : allow for setting number of features for models
# currently equal to image size
#TODO : save current batch id AND ordered data; OR simply allow saving only on epoch change
# this is to prevent messing with the ordering of mid-epoch data used for training
# which defeats the purpose of stochastic batching

KNIFER_ARCHS = {
    "DCGAN": DCGANTrainer,
    "WGAN_GP": WGAN_GPTrainer,
}

## helper class to handle launching epochs, checkpointing, visualization
## meant to be used by the GUI
class TrainingManager():
    def __init__(self, debug=False):
        self.epoch = 0
        self.dataset_folder = None
        self.debug = debug

    def _log(self, text):
        if self.debug:
            print(text)

    def set_dataset_folder(self, folder):
        self.dataset_folder = folder

    def set_trainer(self, params):
        self.trainer = None
        if (torch.cuda.is_available()): ## may or may not work
            torch.cuda.empty_cache()
        self.epoch = 0
        self.batch = 0
        self.params = params
        arch = params["arch"]
        img_size = params["img_size"]
        ## TODO : allow for setting up transformations and augmentations
        self.dataset = dset.ImageFolder(self.dataset_folder, transforms.Compose([
            transforms.Resize(img_size),
            transforms.CenterCrop(img_size),
            transforms.ToTensor(),
            transforms.Normalize((0.5,0.5,0.5),(0.5,0.5,0.5)),
        ]))
        try:
            self.trainer = KNIFER_ARCHS[arch](self.dataset, params) 
            ## may lead to unused params being passed
            ## who cares ?
        except KeyError as e:
            print(f"Parameter {e.args[0]} required by {arch}.")

        if not self.trainer:
            print("Trainer initialization failed.")


        self.fixed = self.trainer.get_fixed()

    def proceed(self, data, batch_id):
        try:
            (batch, labels) = next(data)
            self.batch = batch_id
            self._log("epoch", self.epoch, "batch", batch_id)
            self.trainer.process_batch(batch, labels)
            return batch_id + 1
        except StopIteration:
            self.epoch += 1
            return 0

    def synthetize_viz(self):
        fixed_fakes = self.trainer.GEN(self.fixed)
        #grid = vutils.make_grid(fixed_fakes, normalize=True)
        #grid_pil = transforms.ToPILImage()(grid).convert("RGB")
        vutils.save_image(fixed_fakes, fp=f"./viz/{self.get_filestamp()}.png")

    ## TODO : allow giving a path
    def save(self):
        state = {
            'dataset': self.dataset_folder,
            'model': self.trainer.serialize(),
            'params': self.params,
            'epoch': self.epoch,
            'batch': self.batch,
        }
        arch = state['params']['arch']
        epoch = state['epoch']
        batch = state['batch']
        torch.save(state, f"./savestates/{self.get_filestamp()}.pth")

    def load(self, path) -> int:
        state = torch.load(path)
        self.set_dataset_folder(state['dataset'])
        self.set_trainer(state['params'])
        self.trainer.deserialize(state['model'])
        self.epoch = state['epoch']
        self.batch = state['batch']
        return self.batch

    def get_filestamp(self) -> str:
        arch = self.params["arch"]
        epoch = self.epoch
        batch = self.batch
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{arch}_{timestamp}_{epoch}-{batch}"