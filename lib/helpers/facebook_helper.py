from facebook_business.adobjects.adsinsights import AdsInsights

BREAKDOWNS_POSSIBLE_VALUES = [
    v for k, v in AdsInsights.Breakdowns.__dict__.items() if not k.startswith("__")
]

ACTION_BREAKDOWNS_POSSIBLE_VALUES = [
    v
    for k, v in AdsInsights.ActionBreakdowns.__dict__.items()
    if not k.startswith("__")
]

AD_OBJECT_TYPES = ["adaccount", "campaign", "adset", "ad", "user"]

LEVELS_POSSIBLE_VALUES = ["ad", "adset", "campaign", "account"]

CMP_POSSIBLE_VALUES = [
    "account_id",
    "adlabels",
    "bid_strategy",
    "boosted_object_id",
    "brand_lift_studies",
    "budget_rebalance_flag",
    "budget_remaining",
    "buying_type",
    "can_create_brand_lift_study",
    "can_use_spend_cap",
    "configured_status",
    "created_time",
    "daily_budget",
    "effective_status",
    "id",
    "issues_info",
    "last_budget_toggling_time",
    "lifetime_budget",
    "name",
    "objective",
    "pacing_type",
    "promoted_object",
    "recommendations",
    "source_campaign",
    "source_campaign_id",
    "spend_cap",
    "start_time",
    "status",
    "stop_time",
    "topline_id",
    "updated_time",
]

# should have done this list comprehension selection but
# some of the fields are obsolet and doesn't work, i took the most important
# ADS_POSSIBLE_VALUES = [v for k,v in AdSet.Field.__dict__.items() if not k.startswith("__")]
ADS_POSSIBLE_VALUES = [
    "account_id",
    "adlabels",
    "asset_feed_id",
    "budget_remaining",
    "campaign",
    "campaign_id",
    "configured_status",
    "created_time",
    "creative_sequence",
    "daily_budget",
    "end_time",
    "lifetime_budget",
    "lifetime_imps",
    "lifetime_min_spend_target",
    "lifetime_spend_cap",
    "name",
    "pacing_type",
    "source_adset",
    "source_adset_id",
    "start_time",
    "status",
]

DATE_PRESETS = [
    v for k, v in AdsInsights.DatePreset.__dict__.items() if not k.startswith("__")
]

DESIRED_FIELDS = {
    "date_start": "date_start",
    "date_stop": "date_stop",
    "account_name": "account_name",
    "account_id": "account_id",
    "ad_id": "ad_id",
    "ad_name": "ad_name",
    "adset_id": "adset_id",
    "adset_name": "adset_name",
    "campaign_id": "campaign_id",
    "campaign_name": "campaign_name",
    "clicks": "clicks",
    "link_clicks": "inline_link_clicks",
    "outbound_clicks": ("outbound_clicks", "outbound_click"),
    "impressions": "impressions",
    "post_engagement": ("actions", "post_engagement"),
    "purchases": ("actions", "omni_purchase"),
    "website_purchases": ("actions", "offsite_conversion.fb_pixel_purchase"),
    "purchases_conversion_value": (
        "action_values",
        "offsite_conversion.fb_pixel_purchase",
    ),
    "website_purchases_conversion_value": ("action_values", "omni_purchase"),
    "website_purchase_roas": (
        "website_purchase_roas",
        "offsite_conversion.fb_pixel_purchase",
    ),
    "objective": "objective",
    "reach": "reach",
    "spend": "spend",
    "video_plays_3s": ("actions", "video_view"),
    "video_plays": ("video_play_actions", "video_view"),
    "video_plays_100p": ("video_p100_watched_actions", "video_view"),
    "video_plays_95p": ("video_p95_watched_actions", "video_view"),
    "video_plays_75p": ("video_p75_watched_actions", "video_view"),
    "video_plays_50p": ("video_p50_watched_actions", "video_view"),
    "video_plays_25p": ("video_p25_watched_actions", "video_view"),
    "age": "age",
    "gender": "gender",
    "account_currency": "account_currency",
}


def get_field_value(row, field):
    return (
        row.get(DESIRED_FIELDS[field], None)
        if isinstance(DESIRED_FIELDS[field], str)
        else get_nested_field_value(row, field)
    )


def get_nested_field_value(row, field):
    if DESIRED_FIELDS[field][0] not in row:
        return None
    nested_field = next(
        (
            x
            for x in row[DESIRED_FIELDS[field][0]]
            if x["action_type"] == DESIRED_FIELDS[field][1]
        ),
        {},
    )
    return nested_field["value"] if nested_field else None
