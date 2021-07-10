is_tuning_phase = True
is_bating_click = False
is_enable_set_trigger_max = False

while True:
    data = pd.read_csv('data.csv')
    x = data['x_value'][-300:]
    y = data['y_value'][-300:]
    if is_tuning_phase and not is_bating_click:
        trigger_max = normal_max
        slope = '-' if y.iloc[-1] < normal_max else '+'
        print(f'min: {normal_min}, max: {normal_max}, avg: {round(normal_avg)}, trigger_max: {trigger_max}')
        is_tuning_phase = False
        is_enable_set_trigger_max = True
        continue

    if is_enable_set_trigger_max:
        print('set max')
        if max(y) > normal_max + 5:
            trigger_max = max(y)
            is_enable_set_trigger_max = False
            is_bating_click = True
            continue

    if is_bating_click and not is_enable_set_trigger_max:
        print('baiting')
        if y.iloc[-1] <= trigger_max - 4:
            print(y.iloc[-1], trigger_max)
            print('Click')
            # click action
            time.sleep(4)
            is_bating_click = False
            is_tuning_phase = True
            continue