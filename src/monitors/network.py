from time import sleep
from redis import Redis
from psutil import net_io_counters

REDIS = Redis()
MEASUREMENT_UNITS = ['K', 'M', 'G', 'T', 'P']


def auto_convert_bytes(bytes_, div_count=0):
    if (converted := bytes_ / 1000) > 1000:
        return auto_convert_bytes(converted, div_count + 1)

    return f'{converted:.1f} {MEASUREMENT_UNITS[div_count]}'


def update_total_bytes(total_bytes_recvd, current_bytes_recvd):
    total_bytes_recvd += current_bytes_recvd
    REDIS.set('total_bytes_recvd', total_bytes_recvd)

    return total_bytes_recvd


def update_max_byte_rate(current_bytes_recvd):
    maximum_bytes_recvd = float(REDIS.get('max_bytes_recvd') or 0)
    if maximum_bytes_recvd < current_bytes_recvd:
        maximum_bytes_recvd = current_bytes_recvd
        REDIS.set('max_bytes_recvd', maximum_bytes_recvd)
    
    return maximum_bytes_recvd


def print_network_stats():
    interval_sec = 1
    bytes_recvd_this_session = 0
    bytes_recvd_curr_total = net_io_counters().bytes_recv
    total_bytes_recvd = float(REDIS.get('total_bytes_recvd') or 0)

    while True:
        bytes_recvd_prev_total = bytes_recvd_curr_total
        try:
            bytes_recvd_curr_total = net_io_counters().bytes_recv
        except OSError:
            pass
        else:
            current_bytes_recvd = bytes_recvd_curr_total - bytes_recvd_prev_total

            bytes_recvd_this_session += current_bytes_recvd
            total_bytes_recvd = update_total_bytes(total_bytes_recvd, current_bytes_recvd)
            maximum_bytes_recvd = update_max_byte_rate(current_bytes_recvd / interval_sec)

            total_bytes = auto_convert_bytes(total_bytes_recvd)
            session_bytes = auto_convert_bytes(bytes_recvd_this_session)
            current_byte_rate = auto_convert_bytes(current_bytes_recvd / interval_sec)
            maximum_byte_rate = auto_convert_bytes(maximum_bytes_recvd / interval_sec)

            print(
                f'\rDATA: ({total_bytes}B, {session_bytes}B)    '
                f'RATE: ({maximum_byte_rate}B/s, {current_byte_rate}B/s)    ',
                end='', flush=True
            )

        sleep(interval_sec)


print_network_stats()
