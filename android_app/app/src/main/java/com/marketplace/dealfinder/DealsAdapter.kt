package com.marketplace.dealfinder

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.cardview.widget.CardView
import androidx.recyclerview.widget.RecyclerView
import com.marketplace.dealfinder.models.Deal

class DealsAdapter(
    private val deals: List<Deal>,
    private val onDealClick: (Deal) -> Unit
) : RecyclerView.Adapter<DealsAdapter.DealViewHolder>() {

    class DealViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val cardView: CardView = view.findViewById(R.id.cardView)
        val titleText: TextView = view.findViewById(R.id.titleText)
        val priceText: TextView = view.findViewById(R.id.priceText)
        val sourceText: TextView = view.findViewById(R.id.sourceText)
        val qualityText: TextView = view.findViewById(R.id.qualityText)
        val scoreText: TextView = view.findViewById(R.id.scoreText)
        val locationText: TextView = view.findViewById(R.id.locationText)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): DealViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_deal, parent, false)
        return DealViewHolder(view)
    }

    override fun onBindViewHolder(holder: DealViewHolder, position: Int) {
        val deal = deals[position]

        holder.titleText.text = deal.title
        holder.priceText.text = deal.getPriceString()
        holder.sourceText.text = deal.source
        holder.qualityText.text = deal.getQualityString()
        holder.scoreText.text = "Score: ${deal.getScoreString()}"

        deal.location?.let {
            holder.locationText.text = it
            holder.locationText.visibility = View.VISIBLE
        } ?: run {
            holder.locationText.visibility = View.GONE
        }

        holder.cardView.setOnClickListener {
            onDealClick(deal)
        }
    }

    override fun getItemCount() = deals.size
}
