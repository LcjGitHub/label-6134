<script setup lang="ts">
import { useAsyncState } from '@vueuse/core'
import { NCard, NStatistic, NSpace } from 'naive-ui'
import { fetchGiftSummary } from '../api/gift'
import type { GiftSummary } from '../types/gift'

const {
  state: summary,
  isLoading,
  execute: reload,
} = useAsyncState<GiftSummary | null>(fetchGiftSummary, null, { immediate: false })

defineExpose({ reload })
</script>

<template>
  <n-spin :show="isLoading">
    <div v-if="summary" class="summary-cards">
      <n-space :size="12" style="width: 100%">
        <n-card class="summary-card summary-card--total">
          <n-statistic
            label="总记录数"
            :value="summary.total_count"
            value-style="color: #18a058; font-size: 24px"
          />
        </n-card>
        <n-card class="summary-card summary-card--taken">
          <n-statistic
            label="已取走"
            :value="summary.taken_count"
            value-style="color: #2080f0; font-size: 24px"
          />
        </n-card>
        <n-card class="summary-card summary-card--pending">
          <n-statistic
            label="待取走"
            :value="summary.pending_count"
            value-style="color: #f0a020; font-size: 24px"
          />
        </n-card>
      </n-space>
    </div>
  </n-spin>
</template>

<style scoped>
.summary-cards {
  margin-bottom: 16px;
}

.summary-card {
  flex: 1;
  min-width: 140px;
  padding: 12px 16px;
}

.summary-card :deep(.n-statistic__label) {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.summary-card :deep(.n-card-body) {
  padding: 4px 0;
}
</style>
