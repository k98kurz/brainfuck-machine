add 4 adp 1 add 1 adp 1 add 1 sdp 2
start1: biz end1
    sub 1 adp 2
    start2: biz end2
        sub 1 adp 1 add 1 adp 1 add 1 sdp 2
    bnz start2 end2:
    sdp 1
    start3: biz end3
        sub 1 adp 2 add 1 sdp 2
    bnz start3 end3:
    adp 2
    start4: biz end4
        sub 1 sdp 1 add 1 adp 1
    bnz start4 end4:
    adp 1
    start5: biz end5
        sub 1 sdp 3 add 1 adp 3
    bnz start5 end5:
    sdp 4
bnz start1 end1:
adp 2 out

