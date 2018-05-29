import torch
import subjectlist as subl
import os
import argparse
import torchsrc

def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def print_network(net):
	num_params = 0
	for param in net.parameters():
		num_params += param.numel()
	print(net)
	print('Total number of parameters: %d' % num_params)

parser = argparse.ArgumentParser()
parser.add_argument('--piece', default='3_3_3', help='1_1_1 | 1_1_3 | 3_3_3 etc.')
parser.add_argument('--epoch', type=int, default=10, help='number of epochs to train for, default=10')
parser.add_argument('--lr', type=float, default=0.0001, help='learning rate, default=0.0001')
parser.add_argument('--finetune',type=bool,default=False,help='fine tuning using true')
parser.add_argument('--fineepoch', type=int, default=5, help='fine tuning starting epoch')


opt = parser.parse_args()
print(opt)

# hyper parameters
epoch_num = opt.epoch
batch_size = 1
lmk_num = 133
learning_rate = opt.lr  #0.0001

finetune = opt.finetune
fineepoch = opt.fineepoch

piece = opt.piece

piece_map = {}
piece_map['1_1_1'] = [0, 	96, 		0,	128, 		0,	88]
piece_map['3_1_1'] = [76,	172, 		0,	128, 		0,	88]
piece_map['1_3_1'] = [0,	96,			92,	220, 		0,	88]
piece_map['3_3_1'] = [76,	172, 		92,	220, 		0,	88]

piece_map['1_1_3'] = [0, 	96, 		0,	128, 		68,	156]
piece_map['3_1_3'] = [76,	172, 		0,	128, 		68,	156]
piece_map['1_3_3'] = [0,	96, 		92,	220, 		68,	156]
piece_map['3_3_3'] = [76,	172, 		92,	220, 		68,	156]

#middle ones
piece_map['2_1_1'] = [38, 	134, 		0,	128, 		0,	88]
piece_map['2_3_1'] = [38, 	134,		92,	220, 		0,	88]
piece_map['2_1_3'] = [38, 	134, 		0,	128, 		68,	156]
piece_map['2_3_3'] = [38, 	134, 		92,	220, 		68,	156]

piece_map['1_2_1'] = [0, 	96, 		46,	174, 		0,	88]
piece_map['3_2_1'] = [76,	172, 		46,	174, 		0,	88]
piece_map['1_2_3'] = [0, 	96, 		46,	174, 		68,	156]
piece_map['3_2_3'] = [76,	172, 		46,	174, 		68,	156]

piece_map['1_1_2'] = [0, 	96, 		0,	128, 		34,	122]
piece_map['3_1_2'] = [76,	172, 		0,	128, 		34,	122]
piece_map['1_3_2'] = [0,	96,			92,	220, 		34,	122]
piece_map['3_3_2'] = [76,	172, 		92,	220, 		34,	122]

piece_map['1_2_2'] = [0, 	96, 		46,	174, 		34,	122]
piece_map['3_2_2'] = [76,	172, 		46,	174, 		34,	122]
piece_map['2_2_2'] = [38, 	134, 		46,	174, 		34,	122]
piece_map['2_1_2'] = [38, 	134, 		0,	128, 		34,	122]
piece_map['2_3_2'] = [38, 	134, 		92,	220, 		34,	122]
piece_map['2_2_1'] = [38, 	134, 		46,	174, 		0,	88]
piece_map['2_2_3'] = [38, 	134, 		46,	174, 		68,	156]



# define paths
train_list_file = '/share4/huoy1/Deep_5000_Brain/sublist/sublist_mni.txt'
working_dir = os.path.join('/share4/huoy1/Deep_5000_Brain/working_dir/',piece)
test_img_dir = '/share4/huoy1/Deep_5000_Brain/testing/mni/T1'
finetune_img_dir = '/share4/huoy1/Deep_5000_Brain/finetune_training/aladin-reg-images-normalized'
finetune_seg_dir = '/share4/huoy1/Deep_5000_Brain/finetune_training/aladin-reg-labels/'


# make img list

if finetune == True:
	out = os.path.join(working_dir, 'finetune_out')
	mkdir(out)
	train_img_subs,train_img_files = subl.get_sub_list(finetune_img_dir)
	train_seg_subs,train_seg_files = subl.get_sub_list(finetune_seg_dir)
	train_dict = {}
	train_dict['img_subs'] = train_img_subs
	train_dict['img_files'] = train_img_files
	train_dict['seg_subs'] = train_seg_subs
	train_dict['seg_files'] = train_seg_files
else:
	out = os.path.join(working_dir, 'test_out')
	mkdir(out)
	train_img_subs, train_img_files, train_seg_subs, train_seg_files = subl.get_sub_from_txt(train_list_file)
	train_dict = {}
	train_dict['img_subs'] = train_img_subs
	train_dict['img_files'] = train_img_files
	train_dict['seg_subs'] = train_seg_subs
	train_dict['seg_files'] = train_seg_files

test_img_subs,test_img_files = subl.get_sub_list(test_img_dir)
test_dict = {}
test_dict['img_subs'] = test_img_subs
test_dict['img_files'] = test_img_files



# load image
train_set = torchsrc.imgloaders.pytorch_loader_allpiece(train_dict,num_labels=lmk_num,piece=piece,piece_map=piece_map)
train_loader = torch.utils.data.DataLoader(train_set,batch_size=batch_size,shuffle=True,num_workers=1)
test_set = torchsrc.imgloaders.pytorch_loader_allpiece(test_dict,num_labels=lmk_num,piece=piece,piece_map=piece_map)
test_loader = torch.utils.data.DataLoader(test_set,batch_size=batch_size,shuffle=False,num_workers=1)

# load network
model = torchsrc.models.UNet3D(in_channel=1, n_classes=lmk_num)
# model = torchsrc.models.VNet()

# print_network(model)
#
# load optimizor
optim = torch.optim.Adam(model.parameters(), lr = learning_rate, betas=(0.9, 0.999))
# optim = torch.optim.SGD(model.parameters(), lr=learning_curve() _rate, momentum=0.9)

# load CUDA
cuda = torch.cuda.is_available()
torch.manual_seed(1)
if cuda:
	torch.cuda.manual_seed(1)
	model = model.cuda()

# load trainer
trainer = torchsrc.Trainer(
	cuda=cuda,
	model=model,
	optimizer=optim,
	train_loader=train_loader,
	test_loader=test_loader,
	out=out,
	max_epoch = epoch_num,
	batch_size = batch_size,
	lmk_num = lmk_num,
	finetune = finetune,
	fineepoch = fineepoch
)


print("==start training==")

start_epoch = 0
start_iteration = 1
trainer.epoch = start_epoch
trainer.iteration = start_iteration
trainer.train_epoch()







