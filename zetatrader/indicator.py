#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
import numpy as np
from numpy_ext import rolling_apply

# ======================= #
# PRICE ADJUSTMENT        #
# ======================= #
def remove_variance_effect(ts, alpha, use_ema=True, return_std=False):
    """Removes the variance effect from the first difference of
    given ts series and restore the log-time series indexed at 1000.

    Args:
        ts ([type]): Time Series to remove variance effect
        alpha ([type]): alpha to apply to exponential average of standard dev
        return_std (bool, optional): Log price after removing volatility or
            a tuple with log-price and the return standard deviation

    Returns:
        [type]: [description]
    """
    if use_ema:
        rtn = np.log(ts) - np.log(ts.shift(1))
        # Compute rolling volatility
        rtn_sd = rtn.shift(1).ewm(alpha=alpha).std()
        rtn = (rtn) / rtn_sd

        # Restore time series as log(ts)
        rtn.iloc[1] = np.log(ts.iloc[1])
        if return_std:
            return (rtn.cumsum(), rtn_sd)
        else:
            return rtn.cumsum()
    else:
        window = int(1 / alpha)
        rtn = np.log(ts) - np.log(ts.shift(1))
        # Compute rolling volatility
        rtn_sd = rtn.shift(1).rolling(window).std()
        rtn = (rtn) / rtn_sd

        # Restore time series as log(ts)
        rtn.iloc[1] = np.log(ts.iloc[1])
        if return_std:
            return (rtn.cumsum(), rtn_sd)
        else:
            return rtn.cumsum()


# ======================= #
# DESCRIPTIVE INDICATORS  #
# ======================= #
def percent2max(ts, window):
    rollmax = ts.rolling(window).max()
    return abs(rollmax / ts - 1)


def percent2min(ts, window):
    rollmin = ts.rolling(window).min()
    return abs(rollmin / ts - 1)


# ================= #
# TREND INDICATORS  #
# ================= #
def moving_average_difference(ts, fast_period, slow_period):
    """Returns the difference between the fast and slow moving average.

    Args:
        ts (pd.Series): pandas series to use
        fast_period (int): fast moving average window
        slow_period (int): slow moving average window

    Returns:
        [type]: [description]
    """
    fast = ts.rolling(fast_period).mean()
    slow = ts.rolling(slow_period).mean()
    return fast - slow


def moving_average_pct_difference(ts, fast_period, slow_period):
    """Returns the percentage difference between the fast and slow moving
    average (i. e. how many percent is the the fast period moving average
    above or below the slow moving average). This is useful for
    standardizing moving averages across difference time series.

    Args:
        ts (pd.Series): pd.Series of our time series
        fast_period (int): The fast moving average window
        slow_period (int): The slow moving average window

    Returns:
        [pd.Series]: pandas Series object of the product.
    """
    fast = ts.rolling(fast_period).mean()
    slow = ts.rolling(slow_period).mean()
    return (fast / slow) - 1


def moving_average_openclose_pct_difference(open_px, close_px, period):
    """Compute the difference between average close and average open as
    a percentage of the average open.

    Args:
        open_px (pd.Series): pandas Series of open price
        close_px (pd.Series): pandas Series of close price
        period (int): The rolling period to use

    Returns:
        [pd.Series]: A pandas Series the open close percentage series.
    """
    open_avg = open_px.rolling(period).mean()
    close_avg = close_px.rolling(period).mean()
    return (close_avg / open_avg) - 1


# ================= #
# FILTER INDICATORS #
# ================= #
# def signal2noise(signal, noise, window):
#     """Signal to Noise Ratio based on the formula of
#     variance between signal and noise.

#     Args:
#         signal (pd.Series): signal series
#         noise (pd.Series): noise series
#         window (int): window for rolling variance

#     Returns:
#         [pd.Series]: SNR series
#     """
#     return signal.rolling(window).var() / noise.rolling(window).var()
def signal2noise(ts, window):
    """Returns rolling signal-to-noise ratio computed from dividing return
    with the sum aboslute return of each bar between window given.

    Args:
        ts ([type]): pandas Series
        window ([type]): Window to compute return and noise

    Returns:
        [type]: [description]
    """
    sig = abs(np.log(ts) - np.log(ts.shift(window)))
    diff = abs(np.log(ts) - np.log(ts.shift(1)))
    noise = diff.rolling(window).sum()
    snr = sig / noise
    return snr


def comb_signal2noise(signal, noise, windows):
    """Compute combine signal to noise ratio by computing
    product of all signal-to-noise ratios.

    Args:
        signal (pd.Series): Series of signal
        noise (pd.Series): Series of noise
        windows (int): Rolling window size

    Returns:
        [pd.Series]: Series of signal-to-noise
    """
    snr = signal / signal
    for i in windows:
        snr = snr * signal2noise(signal, noise, i)
    return snr


# ================================ #
#  TRIPLE BARRIER LABELING         #
# ================================ #
def time_to_ceil(close, thresh, base):
    """Returns the number of observations before seeing the first
    observation that is larger than thresh. If none is found, return base

    Args:
        close ([type]): array of close price from current bar to next n-bars
        thresh ([type]): threshold for close to beat
        base ([type]): default value to return if no value is above thresh

    Returns:
        int: The bar that first go above thresh or base if none
    """
    close = close[1:] >= thresh
    if len(np.where(close)[0]) < 1:
        return base
    else:
        return np.where(close)[0][0] + 1


def time_to_floor(close, thresh, base):
    """Returns the number of observations before seeing the first
    observation that is less than thresh. If none is found, return base

    Args:
        close ([type]): array of close price from current bar to next n-bars
        thresh ([type]): threshold for close to beat
        base ([type]): default value to return if no value is below thresh

    Returns:
        int: The bar that first go above thresh or base if none
    """
    close = close[1:] <= thresh
    if len(np.where(close)[0]) < 1:
        return base
    else:
        return np.where(close)[0][0] + 1


def thresh_label(df, upper, lower, n):
    """Returns tuple to indicate which barrier is touched and the number of
    observations before touching the barrier.

    Args:
        df ([type]): Price or event
        upper ([type]): The upper barrier
        lower ([type]): The lower barrier
        n ([type]): number of bars we have in the horizon

    Returns:
        tuple: integer of which barrier is touched and number of bars to event.
    """
    if np.isnan(upper[0]) or np.isnan(lower[0]):
        return np.nan
    else:
        up = time_to_ceil(df, upper[0], base=n)
        down = time_to_floor(df, lower[0], base=n)
        if up < down:
            return (1, up)
        elif down < up:
            return (-1, down)
        else:
            return (0, n)


def asym_thresh_label(df, tgt_long, tgt_short, stop_long, stop_short, n):
    """Label triple barrier based on which directional trade will hit its
    barrier first and the number of bars to that barrier.

    Args:
        df ([type]): value to measure in horizon
        tgt_long ([type]): the upper barrier of long trade
        stop_long ([type]): the lower barrier of long trade
        tgt_short ([type]): lower barrier of short trade
        stop_short ([type]): upper barrier of short trade
        n ([type]): number of observations in horizon

    Returns:
        [type]: [description]
    """
    if np.isnan(tgt_long[0]) or np.isnan(tgt_short[0]) or (len(df) < 2):
        return np.nan
    else:
        long_out = thresh_label(df, tgt_long[0:2], stop_long[0:2], n=n)
        short_out = thresh_label(df, stop_short[0:2], tgt_short[0:2], n=n)
        if type(long_out) == tuple and type(short_out) == tuple:
            change = df[-1] - df[0]
            if long_out[0] == 1 and (short_out[0] == 1 or short_out[0] == 0):
                return long_out
            elif short_out[0] == -1 and (long_out[0] == -1 or long_out[0] == 0):
                return short_out
            elif long_out[0] == 1 and short_out[0] == -1:
                if long_out[0] < short_out[0]:
                    return long_out
                else:
                    return short_out
            elif long_out[0] == 0 and short_out[0] == 0:
                # Neither trades stopped or hit targets
                # Then label as closest to upper to lower target
                partial_label = max(
                    [change / (tgt_long[0] - df[0]), change / (df[0] - tgt_short[0])],
                    key=abs,
                )
                if abs(partial_label) > 1:
                    partial_label = partial_label / abs(partial_label)

                return (partial_label, n)
            elif long_out[0] == -1 and short_out[0] == 1:
                # Stopped on both sides
                return (0, min(long_out[1], short_out[1]))
            elif long_out[0] == 0 and short_out[0] == 1:
                partial_label = max([change / (tgt_long[0] - df[0]), 0], key=abs)

                if abs(partial_label) > 1:
                    partial_label = partial_label / abs(partial_label)

                return (partial_label, n)
            elif long_out[0] == -1 and short_out[0] == 0:
                partial_label = max([0, change / (df[0] - tgt_short[0])], key=abs)

                if abs(partial_label) > 1:
                    partial_label = partial_label / abs(partial_label)

                return (partial_label, n)
            else:
                print("Case not covered")
                print(long_out, short_out)


def legacy_triple_barrier_label(ts, tgt_long, tgt_short, stop_long, stop_short, width):
    # TODO: Wrap asym_thresh_label function for pandas dataframe
    label = rolling_apply(
        asym_thresh_label,
        width + 1,
        *[ts, tgt_long, tgt_short, stop_long, stop_short],
        **{"n": width + 1}
    )
    label = label[width:]
    label = np.append(label, np.full(width, np.nan))
    return label


def triple_barrier_label(
    ts, tgt_long, tgt_short, stop_long, stop_short, horizon, use_partials=False
):
    # TODO: Wrap asym_thresh_label function for pandas dataframe
    # TODO: Add lines to Error Check

    width = horizon + 1
    label = []

    if use_partials == True:
        for i in range(len(ts)):
            if i + width < len(ts) - 1:
                label.append(
                    asym_thresh_label(
                        ts[i : i + width],
                        tgt_long[i : i + width],
                        tgt_short[i : i + width],
                        stop_long[i : i + width],
                        stop_short[i : i + width],
                        horizon,
                    )
                )
            else:
                label.append(
                    asym_thresh_label(
                        ts[i:],
                        tgt_long[i:],
                        tgt_short[i:],
                        stop_long[i:],
                        stop_short[i:],
                        len(ts) - 1 - i,
                    )
                )
    else:
        for i in range(len(ts)):
            if i + width < len(ts) - 1:
                label.append(
                    asym_thresh_label(
                        ts[i : i + width],
                        tgt_long[i : i + width],
                        tgt_short[i : i + width],
                        stop_long[i : i + width],
                        stop_short[i : i + width],
                        horizon,
                    )
                )
            else:
                label.append(np.full(horizon, np.nan))

    label = np.array(label)
    return label
