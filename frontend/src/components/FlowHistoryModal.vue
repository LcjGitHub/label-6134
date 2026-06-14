<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useMessage, NModal, NSpin, NTimeline, NTimelineItem, NEmpty } from 'naive-ui'
import { format, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { fetchFlowHistory } from '../api/flowHistory'
import type { FlowHistory, FlowActionType } from '../types/flowHistory'

const props = defineProps<{
  show: boolean
  giftId: number | null
  giftItemName: string
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
}>()

const message = useMessage()

const historyList = ref<FlowHistory[]>([])
const loading = ref(false)

const visible = computed({
  get: () => props.show,
  set: (val: boolean) => emit('update:show', val),
})

const actionTypeConfig: Record<FlowActionType, { label: string; type: 'success' | 'warning' | 'error' | 'info' | 'default' }> = {
  create: { label: '创建', type: 'success' },
  edit: { label: '编辑', type: 'info' },
  mark_taken: { label: '标记已取走', type: 'warning' },
  cancel_reservation: { label: '取消预约', type: 'error' },
}

function formatDateTime(value: string): string {
  try {
    return format(parseISO(value), 'yyyy年M月d日 HH:mm', { locale: zhCN })
  } catch {
    return value
  }
}

async function loadHistory(): Promise<void> {
  if (!props.giftId) return
  loading.value = true
  try {
    historyList.value = await fetchFlowHistory(props.giftId)
  } catch {
    message.error('加载流转历史失败')
  } finally {
    loading.value = false
  }
}

watch(
  () => props.show,
  (newVal) => {
    if (newVal && props.giftId) {
      loadHistory()
    }
  },
)
</script>

<template>
  <n-modal
    v-model:show="visible"
    preset="card"
    :title="`${giftItemName} - 流转历史`"
    style="width: 560px"
    :mask-closable="true"
  >
    <div class="history-container">
      <n-spin :show="loading">
        <div v-if="historyList.length === 0 && !loading" class="empty-state">
          <n-empty description="暂无流转历史记录" />
        </div>
        <n-timeline v-else line-type="dashed">
          <n-timeline-item
            v-for="item in historyList"
            :key="item.id"
            :type="actionTypeConfig[item.action_type]?.type || 'default'"
            :time="formatDateTime(item.operated_at)"
          >
            <template #header>
              <div class="history-header">
                <span class="action-badge" :class="`action-badge--${item.action_type}`">
                  {{ actionTypeConfig[item.action_type]?.label || item.action_type }}
                </span>
                <span class="operator-name">{{ item.operator_nickname }}</span>
              </div>
            </template>
            <div class="history-desc">{{ item.description }}</div>
          </n-timeline-item>
        </n-timeline>
      </n-spin>
    </div>
  </n-modal>
</template>

<style scoped>
.history-container {
  max-height: 520px;
  overflow-y: auto;
  padding: 4px 0;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.action-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.action-badge--create {
  background: #e8f5e9;
  color: #2e7d32;
}

.action-badge--edit {
  background: #e3f2fd;
  color: #1565c0;
}

.action-badge--mark_taken {
  background: #fff3e0;
  color: #ef6c00;
}

.action-badge--cancel_reservation {
  background: #ffebee;
  color: #c62828;
}

.operator-name {
  font-size: 13px;
  color: #666;
}

.history-desc {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  margin-top: 2px;
}
</style>
