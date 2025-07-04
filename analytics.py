"""
OSRS Analytics Module
Advanced analytics for manipulation detection, volatility scoring, and risk analysis
"""

# Global cache for performance
MANIPULATION_CACHE = {}
VOLATILITY_CACHE = {}


def detect_manipulation(item_id, current_price, hourly_data):
    """
    Detect potential price manipulation using statistical analysis
    Returns manipulation score (0-10) and flags
    """
    try:
        cache_key = f"{item_id}_{current_price}"
        if cache_key in MANIPULATION_CACHE:
            return MANIPULATION_CACHE[cache_key]

        flags = []
        score = 0

        if not hourly_data:
            return {'score': 0, 'flags': ['No data'], 'risk_level': 'Unknown'}

        high_vol = hourly_data.get('highPriceVolume', 0)
        low_vol = hourly_data.get('lowPriceVolume', 0)
        total_vol = high_vol + low_vol

        avg_high = hourly_data.get('avgHighPrice', current_price)
        avg_low = hourly_data.get('avgLowPrice', current_price)

        # Flag 1: Unusual volume spikes
        if total_vol > 10000:
            score += 2
            flags.append('High volume spike')

        # Flag 2: Wide spread relative to price
        if avg_high and avg_low:
            spread_ratio = (avg_high - avg_low) / avg_low
            if spread_ratio > 0.1:
                score += 3
                flags.append('Wide price spread')

        # Flag 3: Unbalanced buy/sell ratio
        if high_vol > 0 and low_vol > 0:
            ratio = max(high_vol, low_vol) / min(high_vol, low_vol)
            if ratio > 10:
                score += 2
                flags.append('Unbalanced order flow')

        # Flag 4: Price vs volume inconsistency
        if total_vol > 0 and current_price > 1000:
            expected_vol = max(100, 50000 / current_price)
            if total_vol > expected_vol * 5:
                score += 2
                flags.append('Volume/price inconsistency')

        if score >= 7:
            risk_level = 'High'
        elif score >= 4:
            risk_level = 'Medium'
        elif score >= 2:
            risk_level = 'Low'
        else:
            risk_level = 'Normal'

        result = {
            'score': min(score, 10),
            'flags': flags,
            'risk_level': risk_level
        }

        MANIPULATION_CACHE[cache_key] = result
        return result

    except Exception as e:
        print(f"Error in manipulation detection: {e}")
        return {'score': 0, 'flags': ['Error'], 'risk_level': 'Unknown'}


def calculate_volatility_score(item_id, current_price, hourly_data):
    """
    Calculate volatility score based on price stability
    Higher score = more volatile = higher risk
    """
    try:
        if item_id in VOLATILITY_CACHE:
            return VOLATILITY_CACHE[item_id]

        if not hourly_data:
            return {'score': 5, 'level': 'Unknown', 'coefficient': 0}

        high_price = hourly_data.get('avgHighPrice', current_price)
        low_price = hourly_data.get('avgLowPrice', current_price)

        if high_price and low_price and low_price > 0:
            price_range = (high_price - low_price) / low_price

            if price_range < 0.02:
                score, level = 1, 'Very Low'
            elif price_range < 0.05:
                score, level = 2, 'Low'
            elif price_range < 0.10:
                score, level = 4, 'Medium'
            elif price_range < 0.20:
                score, level = 6, 'High'
            else:
                score, level = 8, 'Very High'
        else:
            score, level, price_range = 5, 'Unknown', 0

        result = {
            'score': score,
            'level': level,
            'coefficient': round(price_range, 4)
        }

        VOLATILITY_CACHE[item_id] = result
        return result

    except Exception as e:
        print(f"Error calculating volatility: {e}")
        return {'score': 5, 'level': 'Unknown', 'coefficient': 0}


def calculate_capital_at_risk(buy_price, volume, ge_limit, volatility_score):
    """Calculate potential capital loss if price moves against you"""
    try:
        max_position = min(volume, ge_limit) if ge_limit else volume
        capital_required = buy_price * max_position

        risk_multiplier = 1 + (volatility_score / 10) * 0.5
        potential_loss_pct = 0.05 + (volatility_score / 10) * 0.1
        potential_loss = capital_required * potential_loss_pct * risk_multiplier

        return {
            'capital_required': capital_required,
            'potential_loss': potential_loss,
            'risk_ratio': potential_loss / capital_required if capital_required > 0 else 0
        }

    except Exception as e:
        return {'capital_required': 0, 'potential_loss': 0, 'risk_ratio': 0}