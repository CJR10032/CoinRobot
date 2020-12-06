==========init_config方法调用了 end==========
校正g_soc_count和g_wicc_gount的值
get_wicc_soc_count方法调用了
2018-09-19 11:27:05 2.0的 get_soc_wicc_data启动了  --------  
 soc_buy_price = 0.0171; soc_sell_price = 0.0174; wicc_buy_price = 0.208; wicc_sell_price = 0.2089
 soc_to_wicc_minus = -0.00664903; wicc_to_soc_minus = 0.00302182; soc_to_wicc_percent = -3.1828; wicc_to_soc_percent = 1.4742
 all_trans_soc_count = 499.024693297; all_trans_wicc_count = 40.7216205821; soc_count = 484.38; wicc_count = 1.23
wicc贵, 卖wicc买soc流程
正式环境调用sell_soc_and_buy_wicc, 卖soc买wicc
{"status": "ok", "data": "12808395966"}
sell_soc_result = 12808395966
0.54
{"status": "ok", "data": "12808400161"}
buy_wicc_result = 12808400161
......卖31.25个soc买2.57979894686个wicc
============================================================================================================================================

 percent = (wicc_sell_price - calc_by_soc(soc_buy_price)) * 100 / calc_by_soc(soc_buy_price)

 percent = (0.2089 - (0.0171 * 9.0907 + 0.0468)) * 100 / (0.0171 * 9.0907 + 0.0468)
 percent = (0.2089 - 0.20225097) * 100 / 0.20225097
 percent = 0.20225097 个点, 就是