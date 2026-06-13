<script setup lang="ts">
import { computed, h, ref, onMounted, watch } from 'vue'
import { useAsyncState } from '@vueuse/core'
import { parse, format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import type { DataTableColumns, SelectOption } from 'naive-ui'
import { NButton, useDialog, useMessage, NSpace } from 'naive-ui'
import { cancelReservation, fetchReservations } from '../api/reservation'
import type { Reservation, ReservationStatus } from '../types/reservation'

const emit = defineEmits<{
  deleted: []
}>()

const dialog = useDialog()
const message = useMessage()

const statusFilter = ref<ReservationStatus | ''>('')

const statusOptions: SelectOption[] = [
  { label: '全部', value: '' },
  { label: '待确认', value: 'pending' },
  { label: '已确认', value: 'confirmed' },
  { label: '已取消', value: 'cancelled' },
]

const statusTagMap: Record<ReservationStatus, { class: string; text: string }> = {
  pending: { class: 'tag tag--pending', text: '待确认' },
  confirmed: { class: 'tag tag--confirmed', text: '已确认' },
  cancelled: { class: 'tag tag--cancelled', text: '已取消' },
}

async function loadReservations(): Promise<Reservation[]> {
  return await fetchReservations(statusFilter.value || undefined)
}

const {
  state: reservations,
  isLoading,
  error,
  execute: reload,
} = useAsyncState(loadReservations, [], { immediate: false })

watch(statusFilter, () => {
  reload()
})

function formatReserveTime(value: string): string {
  try {
    const dt = parse(value, 'yyyy-MM-dd HH:mm:ss', new Date())
    return format(dt, 'yyyy年M月d日 HH:mm', { locale: zhCN })
  } catch {
    return value
  }
}

const columns = computed<DataTableColumns<Reservation>>(() => [
  { title: 'ID', key: 'id', width: 70 },
  {
    title: '预约物品',
    key: 'gift_item_name',
    width: 160,
    render: (row) =>
      row.gift_item_name
        ? h('span', row.gift_item_name)
        : h('span', { class: 'text-muted' }, '物品已删除'),
  },
  { title: '预约人昵称', key: 'reserver_nickname', width: 140 },
  {
    title: '预约时间',
    key: 'reserve_time',
    width: 180,
    render: (row) => formatReserveTime(row.reserve_time),
  },
  {
    title: '预约状态',
    key: 'status',
    width: 110,
    render: (row) =>
      h(
        'span',
        { class: statusTagMap[row.status].class },
        statusTagMap[row.status].text,
      ),
  },
  {
    title: '操作',
    key: 'actions',
    width: 140,
    render: (row) =>
      h('div', { class: 'actions' }, [
        row.status !== 'cancelled'
          ? h(
              NButton,
              {
                size: 'small',
                quaternary: true,
                type: 'error',
                onClick: () => confirmCancel(row),
              },
              { default: () => '取消预约' },
            )
          : h(
              'span',
              { class: 'text-muted' },
              '已取消',
            ),
      ]),
  },
])

function confirmCancel(reservation: Reservation): void {
  dialog.warning({
    title: '确认取消预约',
    content: `确定取消「${reservation.gift_item_name || '未知物品'}」的预约吗？`,
    positiveText: '取消预约',
    negativeText: '返回',
    onPositiveClick: async () => {
      try {
        await cancelReservation(reservation.id)
        emit('deleted')
        await reload()
      } catch (e: any) {
        const msg = e?.response?.data?.error || '取消失败，请重试'
        message.error(msg)
      }
    },
  })
}

onMounted(() => {
  reload()
})

defineExpose({ reload })
</script>

<template>
  <n-spin :show="isLoading">
    <n-alert v-if="error" type="error" title="加载失败" style="margin-bottom: 16px">
      无法获取预约记录，请确认后端服务已启动（端口 6000）。
    </n-alert>

    <n-space style="margin-bottom: 16px">
      <span class="filter-label">状态筛选：</span>
      <n-select
        v-model:value="statusFilter"
        :options="statusOptions"
        style="width: 160px"
        size="small"
      />
    </n-space>

    <n-data-table
      :columns="columns"
      :data="reservations"
      :bordered="false"
      :single-line="false"
      striped
      size="small"
      :pagination="{ pageSize: 10 }"
    />
  </n-spin>
</template>

<style scoped>
:deep(.actions) {
  display: flex;
  gap: 4px;
}

:deep(.tag) {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

:deep(.tag--pending) {
  background: #fff3e0;
  color: #ef6c00;
}

:deep(.tag--confirmed) {
  background: #e8f5e9;
  color: #2e7d32;
}

:deep(.tag--cancelled) {
  background: #ffebee;
  color: #c62828;
}

:deep(.text-muted) {
  color: #999;
  font-size: 12px;
}

.filter-label {
  font-size: 14px;
  color: #666;
}
</style>
