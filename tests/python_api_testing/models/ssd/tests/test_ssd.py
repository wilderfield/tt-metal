import pytest
from loguru import logger

from torchvision.models.detection import (
    SSDLite320_MobileNet_V3_Large_Weights,
    ssdlite320_mobilenet_v3_large as pretrained,
)
import tt_lib
from tt_models.utility_functions import torch_to_tt_tensor_rm
from tt_models.utility_functions import (
    comp_allclose,
    comp_pcc,
)

from tt_models.ssd.tt.ssd import TtSSD


@pytest.mark.parametrize(
    "pcc",
    ((0.99),),
)
def test_ssd_inference(pcc, imagenet_sample_input, reset_seeds):
    device = tt_lib.device.CreateDevice(tt_lib.device.Arch.GRAYSKULL, 0)
    tt_lib.device.InitializeDevice(device)
    tt_lib.device.SetDefaultDevice(device)

    torch_model = pretrained(weights=SSDLite320_MobileNet_V3_Large_Weights.DEFAULT)
    torch_model.eval()

    config = {}

    tt_model = TtSSD(
        config,
        size=(320, 320),
        num_classes=91,
        image_mean=[0.5, 0.5, 0.5],
        image_std=[0.5, 0.5, 0.5],
        score_thresh=0.001,
        detections_per_image=300,
        topk_candidates=300,
        nms_thresh=0.55,
        state_dict=torch_model.state_dict(),
        base_address=f"",
        device=device,
    )
    tt_model.eval()

    input_tensor = imagenet_sample_input
    torch_output = torch_model(input_tensor)

    tt_input = torch_to_tt_tensor_rm(input_tensor, device)
    tt_output = tt_model(tt_input)

    # Compare outputs
    score_pass, pcc_scores = comp_pcc(
        torch_output[0]["scores"], tt_output[0]["scores"], pcc
    )
    labels_pass, pcc_labels = comp_pcc(
        torch_output[0]["labels"], tt_output[0]["labels"], pcc
    )
    boxes_pass, pcc_boxes = comp_pcc(
        torch_output[0]["boxes"], tt_output[0]["boxes"], pcc
    )

    logger.info(comp_allclose(torch_output[0]["scores"], tt_output[0]["scores"]))
    logger.info(pcc_scores)

    logger.info(comp_allclose(torch_output[0]["labels"], tt_output[0]["labels"]))
    logger.info(pcc_labels)

    logger.info(comp_allclose(torch_output[0]["boxes"], tt_output[0]["boxes"]))
    logger.info(pcc_boxes)

    tt_lib.device.CloseDevice(device)

    if score_pass and labels_pass and boxes_pass:
        logger.info("SSD Passed!")

    assert score_pass, f"Model output does not meet PCC requirement {pcc}."
