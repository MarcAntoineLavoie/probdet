"""
Probabilistic Detectron Training Script following Detectron2 training script found at detectron2/tools.
"""
import core
import os
import sys

# This is very ugly. Essential for now but should be fixed.
sys.path.append(os.path.join(core.top_dir(), 'src', 'detr'))

# Detectron imports
import detectron2.utils.comm as comm
from detectron2.checkpoint import DetectionCheckpointer
from detectron2.data import build_detection_test_loader, build_detection_train_loader
from detectron2.engine import DefaultTrainer, launch
from detectron2.evaluation import COCOEvaluator, DatasetEvaluators, verify_results

# DETR imports
# from d2.train_net import Trainer as Detr_Trainer

# Project imports
from core.setup import setup_config, setup_arg_parser


class Trainer(DefaultTrainer):
    @classmethod
    def build_evaluator(cls, cfg, dataset_name):
        """
        Builds evaluators for post-training mAP report.
        Args:
            cfg(CfgNode): a detectron2 CfgNode
            dataset_name(str): registered dataset name

        Returns:
            detectron2 DatasetEvaluators object
        """
        output_folder = os.path.join(cfg.OUTPUT_DIR, "inference")
        evaluators = [COCOEvaluator(dataset_name, cfg, True, output_folder)]
        return DatasetEvaluators(evaluators)

    @classmethod
    def build_test_loader(cls, cfg, dataset_name):
        """
        Builds DataLoader for test set.
        Args:
            cfg(CfgNode): a detectron2 CfgNode
            dataset_name(str): registered dataset name

        Returns:
            detectron2 DataLoader object specific to the test set.
        """
        return build_detection_test_loader(
            cfg, dataset_name)

    @classmethod
    def build_train_loader(cls, cfg):
        """
        Builds DataLoader for train set.
        Args:
            cfg(CfgNode): a detectron2 CfgNode

        Returns:
            detectron2 DataLoader object specific to the train set.
        """
        return build_detection_train_loader(
            cfg)


def main(args):
    # Setup config node
    cfg = setup_config(args,
                       random_seed=args.random_seed)

    # For debugging only
    #cfg.defrost()
    #cfg.DATALOADER.NUM_WORKERS = 0
    #cfg.SOLVER.IMS_PER_BATCH = 1

    # Eval only mode to produce mAP results
    # Build Trainer from config node. Begin Training.
    # if cfg.MODEL.META_ARCHITECTURE == 'ProbabilisticDetr':
    #     trainer = Detr_Trainer(cfg)
    # else:
    trainer = Trainer(cfg)

    if args.eval_only:
        model = trainer.build_model(cfg)
        DetectionCheckpointer(model, save_dir=cfg.OUTPUT_DIR).resume_or_load(
            cfg.MODEL.WEIGHTS, resume=args.resume
        )
        res = trainer.test(cfg, model)
        if comm.is_main_process():
            verify_results(cfg, res)
        return res

    trainer.resume_or_load(resume=args.resume)
    return trainer.train()


if __name__ == "__main__":
    # Create arg parser
    arg_parser = setup_arg_parser()

    args = arg_parser.parse_args()
    print("Command Line Args:", args)

    args.num_gpus=1
    args.dataset_dir='/home/marc/Downloads/COCO_data'
    args.config_file='/home/marc/Documents/trailab_work/uda_detect/probdet/src/configs/COCO-Detection/faster-rcnn/faster_rcnn_R_50_FPN_3x_reg_var_es.yaml'
    args.random_seed=1000
    args.resume=False

    launch(
        main,
        args.num_gpus,
        num_machines=args.num_machines,
        machine_rank=args.machine_rank,
        dist_url=args.dist_url,
        args=(args,),
    )
