<script setup lang="ts">
import { useAsyncState } from '@vueuse/core'
import { NCard, NStatistic } from 'naive-ui'
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
      <n-card class="summary-card summary-card--total">
        <n-statistic label="总记录数" :value="summary.total_count" />
      </n-card>
      <n-card class="summary-card summary-card--taken">
        <n-statistic label="已取走" :value="summary.taken_count" />
      </n-card>
      <n-card class="summary-card summary-card--pending">
        <n-statistic label="待取走" :value="summary.pending_count" />
      </n-card>
    </div>
  </n-spin>
</template>

<style scoped>
.summary-cards {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  width: 100%;
}

.summary-card {
  flex: 1 1 0;
  min-width: 0;
}

.summary-card :deep(.n-card-body) {
  padding: 12px 16px;
}

.summary-card :deep(.n-statistic__label) {
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
}

.summary-card :deep(.n-statistic__value) {
  font-size: 28px;
  font-weight: 600;
  line-height: 1.2;
}

.summary-card--total :deep(.n-statistic__value) {
  color: #18a058;
}

.summary-card--taken :deep(.n-statistic__value) {
  color: #2080f0;
}

.summary-card--pending :deep(.n-statistic__value) {
  color: #f0a020;
}
</style>
