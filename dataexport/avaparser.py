"""
This parses values into a sane format per https://www.documents.philips.com/doclib/enc/fetch/2000/4504/577242/577243/577247/582636/582882/X2%2C_MP%2C_MX_&_FM_Series_Rel._L.0_Data_Export_Interface_Program._Guide_4535_645_88011_(ENG).pdf
"""

def parse_u16(data, index):
    return int.from_bytes(data[index:index+2])

def parse_u32(data, index):
    return int.from_bytes(data[index:index+4])

def parse_float(data, index):
    # This is a weird u32 way to represent floats
    # Lower u8 is a signed exponent, upper u24 is mantissa
    # The number is mantissa * 10^exponent
    exp = data[index+3]
    mantissa = int.from_bytes(data[index:index+3], signed=True)
    return mantissa * pow(10, exp) # We're just ignoring the NaN values

def parse_value(data):
    """
    Parses AVA (Attribute Value Assertion) values
    The data bytes must include the AVA header
    u16 attr_id
    u16 length
    XXX value
    """
    attr_id = parse_u16(data, 0)
    print("ATTR", data[0], data[1])
    length = parse_u16(data, 2)-4
    if attr_id == 0x0950:
        # Numerical observation
        # u16 physio_id, u16 state, u16 unit, float value
        physio_id = parse_u16(data, 4)
        state = parse_u16(data, 6)
        unit = parse_u16(data, 8)
        value = parse_float(data, 10)
        return ("numobs", length+4, physio_id, state, unit, value)
    elif attr_id == 0x0916:
        # Device alert
        # u16 state, u16 al_stat_chg_cnt, u16 max_p_alarm, u16 max_t_alarm, u16 max_aud_alarm
        state = parse_u16(data, 4)
        stat_chg_cnt = parse_u16(data, 6)
        max_p_alarm = parse_u16(data, 8)
        max_t_alarm = parse_u16(data, 10)
        max_aud_alarm = parse_u16(data, 12)
        return ("global_alerts", length+4, state, stat_chg_cnt, max_p_alarm, max_t_alarm, max_aud_alarm)
    elif attr_id == 0x0902 or attr_id == 0x0904:
        # P alarm list
        count = parse_u16(data, 4)
        index = 8
        entries = []
        for i in range(count):
            source = parse_u16(data, index)
            code = parse_u16(data, index + 2)
            type = parse_u16(data, index + 4)
            state = parse_u16(data, index + 6)
            entries.append((source, code, type, state))
            length = parse_u16(data, index + 16)
            index += 16 + length
        return ("alarm", length+4, entries)
    else:
        datas = ""
        for i in range(length):
            if i+4 >= len(data):
                break
            datas += str(data[i]+4) + " "
        return ("unk_" + str(attr_id), length+4, datas)
