<script setup lang="ts">
import { computed, h, onMounted } from 'vue'
import { useAsyncState } from '@vueuse/core'
import { format, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import type { DataTableColumns } from 'naive-ui'
import { NButton, useDialog } from 'naive-ui'
import { deleteGift, fetchGifts } from '../api/gift'
import type { Gift } from '../types/gift'

const emit = defineEmits<{
  edit: [gift: Gift]
  deleted: []
}>()

const dialog = useDialog()

const {
  state: gifts,
  isLoading,
  error,
  execute: reload,
} = useAsyncState(fetchGifts, [], { immediate: false })

/** 格式化赠送日期为中文显示 */
function formatGiftDate(value: string): string {
  try {
    return format(parseISO(value), 'yyyy年M月d日', { locale: zhCN })
  } catch {
    return value
  }
}

const columns = computed<DataTableColumns<Gift>>(() => [
  { title: '物品名', key: 'item_name', width: 140, ellipsis: { tooltip: true } },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  {
    title: '赠送日期',
    key: 'gift_date',
    width: 130,
    render: (row) => formatGiftDate(row.gift_date),
  },
  { title: '接收方昵称', key: 'recipient_nickname', width: 120 },
  {
    title: '是否已取走',
    key: 'is_taken',
    width: 110,
    render: (row) =>
      row.is_taken
        ? h('span', { class: 'tag tag--done' }, '已取走')
        : h('span', { class: 'tag tag--pending' }, '待取走'),
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row) =>
      h('div', { class: 'actions' }, [
        h(
          NButton,
          {
            size: 'small',
            quaternary: true,
            type: 'primary',
            onClick: () => emit('edit', row),
          },
          { default: () => '编辑' },
        ),
        h(
          NButton,
          {
            size: 'small',
            quaternary: true,
            type: 'error',
            onClick: () => confirmDelete(row),
          },
          { default: () => '删除' },
        ),
      ]),
  },
])

/** 确认并删除记录 */
function confirmDelete(gift: Gift): void {
  dialog.warning({
    title: '确认删除',
    content: `确定删除「${gift.item_name}」的赠送记录吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      await deleteGift(gift.id)
      emit('deleted')
      await reload()
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
      无法获取赠送记录，请确认后端服务已启动（端口 6000）。
    </n-alert>

    <n-data-table
      :columns="columns"
      :data="gifts"
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

:deep(.tag--done) {
  background: #e8f5e9;
  color: #2e7d32;
}

:deep(.tag--pending) {
  background: #fff3e0;
  color: #ef6c00;
}
</style>
