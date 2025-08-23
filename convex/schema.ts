import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";
import { authTables } from "@convex-dev/auth/server";

export default defineSchema({
  ...authTables,
  forms: defineTable({
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
    userId: v.optional(v.id("users")),
  }).index("by_user_id", ["userId"]),
  transcripts: defineTable({
    formId: v.id("forms"),
    chunk: v.string(),
  }).index("by_form_id", ["formId"]),
});