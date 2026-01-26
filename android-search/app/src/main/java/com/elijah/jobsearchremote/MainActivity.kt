package com.elijah.jobsearchremote

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import coil3.compose.AsyncImage
import androidx.compose.ui.layout.ContentScale
import io.github.jan.supabase.createSupabaseClient
import io.github.jan.supabase.postgrest.Postgrest
import io.github.jan.supabase.realtime.Realtime
import io.github.jan.supabase.postgrest.from
import io.github.jan.supabase.postgrest.query.Columns
import kotlinx.coroutines.launch

// 1. Setup your credentials (Get these from your Supabase Project Settings > API)
val supabase = createSupabaseClient(
    supabaseUrl = "https://dvjwkduaxvzyoodyfzgr.supabase.co",
    supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR2andrZHVheHZ6eW9vZHlmemdyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjczODIwODMsImV4cCI6MjA4Mjk1ODA4M30.VHM4NuOb3gb8ccDtPDyU2QiUI8WN-tbJKtwUUO6HNkk"
) {
    install(Postgrest)
    install(Realtime)
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            // This is where your UI starts
            Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                JobApprovalScreen()
            }
        }
    }
}

@Composable
fun JobApprovalScreen() {
    // A list that Compose "watches" - if this changes, the UI updates automatically
    val jobs = remember { mutableStateListOf<Job>() }
    val scope = rememberCoroutineScope()

    // Function to update job status in Supabase
    fun updateJobStatus(jobId: String, newStatus: String) {
        scope.launch {
            try {
                supabase.from("jobs").update(
                    {
                        set("status", newStatus)
                    }
                ) {
                    filter { eq("id", jobId) }
                }
                // Remove from local list so it disappears from screen
                jobs.removeAll { it.id == jobId }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    // This block runs once when the screen opens
    LaunchedEffect(Unit) {
        scope.launch {
            try {
                // Fetch jobs that are 'Pending Approval'
                val results = supabase.from("jobs")
                    .select {
                        filter { eq("status", "Pending Approval") }
                    }.decodeList<Job>()

                jobs.clear()
                jobs.addAll(results)
            } catch (e: Exception) {
                // Handle errors (like no internet)
                println("Error fetching jobs: ${e.message}")
            }
        }
    }

    // The actual Layout
    Column(modifier = Modifier.padding(16.dp)) {
        Text(text = "Pending Approvals", style = MaterialTheme.typography.headlineMedium)

        LazyColumn {
            items(jobs) { job ->
                JobCard(job = job, onAction = { status ->
                    updateJobStatus(job.id, status)
                })
            }
        }
    }
}

@Composable
fun JobCard(job: Job, onAction: (String) -> Unit) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        elevation = CardDefaults.cardElevation(4.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = job.job_title, style = MaterialTheme.typography.headlineSmall)
            Text(text = job.company_name, style = MaterialTheme.typography.bodyLarge)

            Spacer(modifier = Modifier.height(8.dp))

            // 1. Display the Screenshot
            // Inside your JobCard function
            if (!job.screenshot_url.isNullOrEmpty()) {
                AsyncImage(
                    model = job.screenshot_url,
                    contentDescription = "Job Screenshot",
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(250.dp)
                        .padding(vertical = 8.dp),
                    contentScale = ContentScale.Fit // This ensures the whole screenshot is visible
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            // 2. Action Buttons
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                Button(
                    onClick = { onAction("Rejected") },
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                ) {
                    Text("Reject")
                }
                Button(
                    onClick = { onAction("Approved") },
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                ) {
                    Text("Approve")
                }
            }
        }
    }
}