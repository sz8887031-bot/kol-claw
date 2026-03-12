#!/bin/bash

# 自动化抓取脚本 - 持续执行直到达到15个优质达人

MEDIACRAWLER_DIR="<MEDIACRAWLER_DIR>"
PROJECT_DIR="<PROJECT_DIR>"
TARGET_COUNT=15

# 批次数据
BATCH_1="MS4wLjABAAAA-e4mMCZ3AAIVsd3zezzHJtSjZZmocBsEK00NxaUOChrbcVWOAwrMSvx2-Du7uztB,MS4wLjABAAAA07kCFhlVBc6eb1RtfhYGD0bncCltZZIDFJGSe7cFO_wffRPk5yVGmXiU1pRwvtbJ,MS4wLjABAAAA0Lqxah5HwgqYqOsNnG7vVz-kQAGtLXGLDk_IWXFG-S0,MS4wLjABAAAA18CTId2ob9wtcztpaq_KejhsQrT9b8rR-HMnP_jO7Pw,MS4wLjABAAAA1eBmtxiAR7IlL0Hq6oXxMb3Fsnk7yc3QH0OCrnRyy9GYYinCFzAaF2QDs2n-Qjow,MS4wLjABAAAA21mChZUlKQ5fPEpGl0oohH3v9iR2AlrVg7sYHHpwh-c21foOKIXIO06Bz5PIYnH2,MS4wLjABAAAA2TCx8Hhm0wGJG3E7Gqh0cKvC1eHAELptETYhAn3um00,MS4wLjABAAAA2nxhY4wWf8a6dn9QRpfmqtR3kadD5lh8D2Ank1wi_RjAKf3YTZbIgJDRKug2YVU0,MS4wLjABAAAA38Efw1E8rRpxBCcmU1uy0fGlK6EEcEMdIrQgy3vQKsQ,MS4wLjABAAAA3IgCPwiFrmRyCb18E67T86DUpVIB8ytwIpxEx36SIOPYt2thGN6q5RYbtTG1XSld,MS4wLjABAAAA3JWz6CSvIqcBeH6G0d17ZRpTFOmTV6BR42lXc-n-VaCSfnU630Sr-jm1GlTIuFn1,MS4wLjABAAAA3lj_QofYZ8Map4Z0sUjOL5ImLF1pmHHhgC5jfw_TQ70,MS4wLjABAAAA4LTPN0pbViDjx1UzlT9UPBy0RJ1v_NjakB8hCz9PklM,MS4wLjABAAAA4MijIV3H9FMFYKlLgyCTPW35J0yBKmvW5WhJk0uiv3yNcRUwNo5hp-OalhQUxxZ4,MS4wLjABAAAA4O2cpmZXO4reZaDG1gD1mXf_kYjLzLj6B4WxAeDokSV75wY3SYDLTGxkxVGrAZgS,MS4wLjABAAAA595jo4vAushZUzOfbpPSadhFo1BtGWA_wPag-UVntUE,MS4wLjABAAAA5roowra_1Q9ryBMb_D7QB_CPd_jBMMeqB1ey6C8GTDtbGMPk8OSrpuUnSDCD_A0Q,MS4wLjABAAAA6bgRDCXAhouqQVv8QWt8P5MD12HOwp88PUeG6VC7grKnTsg_5OTFtY96YTlOYrEb,MS4wLjABAAAA92VJD0PYEwb2P3l_1RvuVjijaKkRUFMawcZLDlFOW4s,MS4wLjABAAAAAPGWUPF47mNybyCjjGhJgw3a088sHLq25OVa9B2Ztsy4jrDiQmVx3sdHOhT-ehHz,MS4wLjABAAAAAjB8_i91R90IHafPY-0aMlyS7ApM_hOE3Qz497rf9BL_k37hCHbt2mrPdrCQceLF,MS4wLjABAAAABf-sr4LOMnm4nrn0gg0pgPD3mviIxwj_E3JTl0G3vCI,MS4wLjABAAAABigrDMr8D7NTnWFEqGzhRsYuK4RGaysdIm5fS5SgWNc,MS4wLjABAAAABrqVyqvweV8GVNe6avoxqe8IbtauC9eKibGRCBAJ9Nynl9Nc53CvzjbfNEyqSVbi,MS4wLjABAAAAChCQKs069Ma5VNHkqTGC_KvTnrZwqc0d1500uatfAIU,MS4wLjABAAAAD3RD3hmYW7L4YLUe-8eLt1_H4NBGLI4DN0ysEzKvIR4wDGAAaU_zzJrdpj80eCr_,MS4wLjABAAAADF4-IXU8jZmuZSBeEw13MzdsQ5O1KwOjVjccIjIePhGVokQjRH6DZQuM3sNDwwBt,MS4wLjABAAAADPk7EX-LchHkhkuvCHDcbPDGjd4PCi0Gs6zRE5mI7Hc,MS4wLjABAAAADRKQjzTYk9aMu87-PS2hDDiKDB4Fh0UkeSLm0Vba_SE-mb8iYKIhac74fYqF-L2P,MS4wLjABAAAADkCy14YeBlqdS-33a6ZhNsEDACO-Gk5Ar8QjXEY3XUn96N_euj-i1ov2Jszqy3LM"

BATCH_2="MS4wLjABAAAADwioQ9TzNfeREBu5Hmu5TMbP03UEj7MZIq1Ozg3P7zSoCJPo1Z7dMV4yh1b_vPmf,MS4wLjABAAAAEhA8Bfyea2fz3s4an14XNXCknqk4BPIacTwIbMGDRdS8Ohh3VD-rmQUq9tcG_BE-,MS4wLjABAAAAEoqGNwfAE1gNkRPlixQCqbXA5ylb1gzK8uWfp7qKZhJUbAyqw6W4wmIl29x6dzDW,MS4wLjABAAAAFQdxwG4t3fnMoUoN-aniDbceUGuuB2HXNbSvq2zK18muQrnrEY2N2pyy4xPHqUHO,MS4wLjABAAAAFe245otQwpiAXSln49a7BdVO-PnquC_82o_Gg6BFCXTqJJAofGh_O2s_ea5m7FfV,MS4wLjABAAAAGHXUkEOU7i7jxXbGirena6f-GzOMVVRwoJa83RrE6tDujKmYRxfegeUo-hoR5cMg,MS4wLjABAAAAGHYX8K1BoWwsEKD9H1lD_SOb-jgT4ZFM81PTXAaE3TEx5hkwnbEucmyhI2utgRKv,MS4wLjABAAAAGV0e3dQAIGyNVG-Nh776IniAgw3i225TMKrEgG29jpe9hrbA_wRuezOIfxHvsAKb,MS4wLjABAAAAGqQ4SrwqZeN6v-H_HfsyIDfv7D0JXk72bC16tyK0_dSX2UvsyMynJOA55CJKrVYe,MS4wLjABAAAAIKbE2m0qrLEtxCG88yxhq_dBpQa6xsMieJ6z_VqnRI-Irip7ykxvLrGsj5LjfLY0,MS4wLjABAAAAIi118VDEwBXG0OFgAdXs9LU8gjy9CPHo1lGIwPEHaK7_QBsC6aXT42ziMrUnj0MK,MS4wLjABAAAAInLg-0w0LveAi4J_tAflb9ni87Qp2v-L_WWEscsdmTQyoPAwD33XajuUn9a8S5wI,MS4wLjABAAAAIpwck2syUGUf76iuLi0leRa6Wg2JDUVyaG0WMy-PzqQ2_yAt_bMNCfUGqHuqD0fW,MS4wLjABAAAAIu8jpvOW6TUskaH-q8b3Z2jT2DDeZ382SFcoE1N0GA4,MS4wLjABAAAAJSKC7nhyGBMOSP-XH65rl4xgm-RnkIC6qww1g2SUX2Q,MS4wLjABAAAAK4kLEqbIlBvoT7BLWK5FlexojZleufW3riv7IK3cgJ4,MS4wLjABAAAALg65hGp6oDu-KXi1q6TLCjqc09bA9q9OD2CQPmmuJhE,MS4wLjABAAAALn-WYwPCCSE6PU1L5MNyYUpGc93WgqrGMbDZNEF_oPo,MS4wLjABAAAAM4gmiT1JI-1b7wKw_AH37aJjy79ISffLF7RXjO1yftE1SLT8wKWn1wWHDo6SKipY,MS4wLjABAAAAMV6EhNBnJJ87NN2DFgC71sK5D-A0kLRdq_aIcuUq3-M,MS4wLjABAAAAMX4jc9lu98KHlzgSJL2C6r9e2E0i1X_WHjWoEi-eqUfQ53dq1LEpqtc0bdoavm-W,MS4wLjABAAAAN072cpRG6Ascc27mTfEvKj07hvclZfsDrjCqg3PzHZTYZ0WEknPaW61-qYa422MH,MS4wLjABAAAANUG74nzznnA7Q1Wzfwm4JGS0UTghGm1_HnRLL32z3daa76bQx0xjn_5fS329wt1t,MS4wLjABAAAAOSRJydMqjThfh_AfKsRlCwj9jxjORPOza0qpRYopXLhQUwei_MTbZ362w8n2rbv1,MS4wLjABAAAAPCIrapiMeTdh-CF0CMPa7jkXQUHKjF0aAc-VCdwWnCArfM-eYafyjJqNft9k2S0X,MS4wLjABAAAAPDscF1fBg90C5KSAL5TZIAV_DemJbnyP3wrejsvWE6Pd2G0q5tM-iaTLbAlW3cye,MS4wLjABAAAAPMmSRO1STnp0C7fSOp8L-5PBX98epk-RIMJKE--9FvgrwAgmlvO8J_d7v2Ab7Qlo,MS4wLjABAAAAQElwgqjTGhKwpVn9EHbGK4e21QPbCmfXu8_bzB59P8dKPRCJUjIi9CPTond643xV,MS4wLjABAAAAQnPxBuIheu3hs7X2OtNvnqGNWyu2_PcYzRxeTUHD5aY,MS4wLjABAAAAR1x8BRjGnvAlsrsYHGCTZ7qorJ_AVR1N4Dr2dAoJnyiBlBkFdkVCagKlfy55TrOS"

echo "========================================="
echo "自动化抓取任务开始"
echo "目标：累计${TARGET_COUNT}个优质达人（S/A级）"
echo "========================================="

# 函数：检查优质达人数量
check_quality_count() {
    local count=$(grep -c "A级\|S级" "$PROJECT_DIR/data/优质达人.csv" 2>/dev/null || echo "0")
    echo $count
}

# 函数：执行批次抓取
run_batch() {
    local batch_num=$1
    local batch_ids=$2

    echo ""
    echo ">>> 批次${batch_num}开始抓取（30个达人）"
    echo ">>> 时间：$(date '+%Y-%m-%d %H:%M:%S')"

    cd "$MEDIACRAWLER_DIR"
    python3 main.py --platform dy --lt qrcode --type creator --creator_id "$batch_ids"

    echo ">>> 批次${batch_num}抓取完成"

    # 分析数据
    echo ">>> 运行数据分析..."
    cd "$PROJECT_DIR"
    python3 data/process_mediacrawler_data_v2.py

    # 检查优质达人数量
    local current_count=$(check_quality_count)
    echo ">>> 当前优质达人数量：${current_count}/${TARGET_COUNT}"

    return $current_count
}

# 执行批次1
run_batch 1 "$BATCH_1"
CURRENT_COUNT=$?

if [ $CURRENT_COUNT -ge $TARGET_COUNT ]; then
    echo ""
    echo "========================================="
    echo "✅ 已达到目标！优质达人数量：${CURRENT_COUNT}"
    echo "========================================="
    exit 0
fi

# 执行批次2
run_batch 2 "$BATCH_2"
CURRENT_COUNT=$?

if [ $CURRENT_COUNT -ge $TARGET_COUNT ]; then
    echo ""
    echo "========================================="
    echo "✅ 已达到目标！优质达人数量：${CURRENT_COUNT}"
    echo "========================================="
    exit 0
fi

echo ""
echo "========================================="
echo "批次1-2完成，当前优质达人：${CURRENT_COUNT}/${TARGET_COUNT}"
echo "需要继续执行更多批次"
echo "========================================="
