import random
#Degree Probability
deg_dist = [
(19,	0.01),
(25,	0.03),
(29,	0.04),
(35,	0.025),
(38,	0.035),
(45,	0.02),
(49,	0.025),
(53,	0.015),
(58,	0.02),
(65,	0.02),
(67,	0.015),
(73,	0.015),
(78,	0.015),
(82,	0.015),
(89,	0.015),
(94,	0.015),
(99,	0.015),
(102,	0.02),
(107,	0.02),
(113,	0.04),
(118,	0.1),
(125,	0.19),
(129,	0.135),
(133,	0.05),
(139,	0.015),
(144,	0.005),
(150,	0.005),
(155,	0.005),
(160,	0.005),
(168,	0.005),
(177,	0.005),
(185,	0.005),
(190,	0.005),
(197,	0.005),
(230,	0.005),
(235,	0.005),
(250,	0.005),
(260,	0.005),
(267,	0.005),
(272,	0.005),
(285,	0.0025),
(290,	0.0025),
(298,	0.0025),
(308,	0.0025),
(317,	0.0025),
(328,	0.0025),
(340,	0.0025),
(351,	0.0025),
(365,	0.0025),
(376,	0.0025),
(398,	0.005),
(422,	0.005),
(474,	0.005),
(492,	0.0025)
]


deg_space = []
for deg, prob in deg_dist:
    count = int(10000 * prob)
    for i in range(0, count):
        r_deg = random.randint(max(deg-2, 1), deg+3)
        deg_space.append(deg)


#plot random sample:
sample = random.sample(deg_space, 1000)
