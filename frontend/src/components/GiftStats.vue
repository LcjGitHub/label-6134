<script setup lang="ts">
import { onMounted } from 'vue'
import { useAsyncState } from '@vueuse/core'
import { NCard, NStatistic, NList, NListItem, NSpace } from 'naive-ui'
import { fetchGiftStats } from '../api/gift'

const {
  state: stats,
  isLoading,
  error,
  execute: reload,
} = useAsyncState(fetchGiftStats, null, { immediate: false })

function formatMonth(month: string): string {
  const [year, m] = month.split('-')
  return `${year}年${parseInt(m, 10)}月`
}

onMounted(() => {
  reload()
})

defineExpose({ reload })
</script>

<template>
  <n-spin :show="isLoading">
    <n-alert v-if="error" type="error" title="加载失败" style="margin-bottom: 16px">
      无法获取统计数据，请确认后端服务已启动（端口 6000）。
    </n-alert>

    <div v-if="stats" class="stats-container">
      <n-space :size="16" style="width: 100%; margin-bottom: 24px">
        <n-card class="stat-card">
          <n-statistic
            label="赠送记录总数"
            :value="stats.total_count"
            value-style="color: #18a058"
          />
        </n-card>
        <n-card class="stat-card">
          <n-statistic
            label="已取走数量"
            :value="stats.taken_count"
            value-style="color: #2080f0"
          />
        </n-card>
        <n-card class="stat-card">
          <n-statistic
            label="待取走数量"
            :value="stats.pending_count"
            value-style="color: #f0a020"
          />
        </n-card>
      </n-space>

      <n-card title="各月赠送数量汇总" style="width: 100%">
        <n-list v-if="stats.monthly_stats.length > 0" bordered>
          <n-list-item v-for="item in stats.monthly_stats" :key="item.month">
            <div class="month-item">
              <span class="month-label">{{ formatMonth(item.month) }}</span>
              <span class="month-count">{{ item.count }} 件</span>
            </div>
          </n-list-item>
        </n-list>
        <div v-else class="empty-tip">
          暂无数据
        </div>
      </n-card>
    </div>
  </n-spin>
</template>

<style scoped>
.stats-container {
  padding: 20px;
}

.stat-card {
  flex: 1;
  min-width: 200px;
}

.month-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.month-label {
  font-size: 14px;
  color: #333;
}

.month-count {
  font-size: 14px;
  font-weight: 600;
  color: #18a058;
}

.empty-tip {
  text-align: center;
  color: #999;
  padding: 40px 0;
  font-size: 14px;
}
</style>
