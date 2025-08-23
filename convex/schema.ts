import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // DS-160 data collection records
  collections: defineTable({
    // Call identification
    callId: v.string(),

    // Collection status
    status: v.union(
      v.literal("in_progress"),
      v.literal("completed"),
      v.literal("failed"),
      v.literal("abandoned")
    ),

    // Timestamps
    completedAt: v.optional(v.string()),
  }),
  transcripts: defineTable({
    connectionId: v.string(),
    transcript: v.string(),
  }).index("by_connection_id", ["connectionId"]),
});