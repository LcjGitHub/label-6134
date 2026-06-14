<script setup lang="ts">
import { computed, h, onMounted } from 'vue'
import { useAsyncState } from '@vueuse/core'
import type { DataTableColumns } from 'naive-ui'
import { NButton, useDialog } from 'naive-ui'
import { deleteLocation, fetchLocations } from '../api/location'
import type { Location } from '../types/location'

const emit = defineEmits<{
  edit: [location: Location]
  deleted: []
}>()

const dialog = useDialog()

const {
  state: locations,
  isLoading,
  error,
  execute: reload,
} = useAsyncState(fetchLocations, [], { immediate: false })

const columns = computed<DataTableColumns<Location>>(() => [
  { title: '序号', key: 'sort_order', width: 100 },
  { title: '地点名称', key: 'name', ellipsis: { tooltip: true } },
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

function confirmDelete(location: Location): void {
  dialog.warning({
    title: '确认删除',
    content: `确定删除地点「${location.name}」吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await deleteLocation(location.id)
        emit('deleted')
        await reload()
      } catch (e: any) {
        const msg = e?.response?.data?.error || '删除失败'
        dialog.error({
          title: '删除失败',
          content: msg,
          positiveText: '知道了',
        })
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
      无法获取地点列表，请确认后端服务已启动（端口 6000）。
    </n-alert>

    <n-data-table
      :columns="columns"
      :data="locations"
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
</style>
