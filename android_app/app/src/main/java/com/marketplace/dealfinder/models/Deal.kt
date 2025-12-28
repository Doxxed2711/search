package com.marketplace.dealfinder.models

import android.os.Parcelable
import kotlinx.parcelize.Parcelize

@Parcelize
data class Deal(
    val title: String,
    val price: Double,
    val url: String,
    val source: String,
    val location: String?,
    val confidence_score: Double?,
    val deal_quality: String?
) : Parcelable {

    fun getPriceString(): String = "$%.2f".format(price)

    fun getQualityString(): String = deal_quality?.uppercase() ?: "UNKNOWN"

    fun getScoreString(): String = confidence_score?.let {
        "%.1f/100".format(it)
    } ?: "N/A"
}
