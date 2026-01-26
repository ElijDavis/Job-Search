package com.elijah.jobsearchremote

import kotlinx.serialization.Serializable

@Serializable
data class Job(
    val id: String,
    val company_name: String,
    val job_title: String,
    val status: String,
    val screenshot_url: String? = null,
    val match_score: Int = 0
)