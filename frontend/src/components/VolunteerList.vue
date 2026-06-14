<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue'
import { useAsyncState, watchDebounced } from '@vueuse/core'
import { format, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import type { DataTableColumns, SelectOption } from 'naive-ui'
import { NButton, NDescriptions, NDescriptionsItem, NModal, NSpace, useDialog } from 'naive-ui'
import { deleteVolunteer, fetchVolunteers, type VolunteerQueryParams } from '../api/volunteer'
import type { Volunteer } from '../types/volunteer'

const emit = defineEmits<{
  edit: [volunteer: Volunteer]
  deleted: []
}>()

const dialog = useDialog()

const searchKeyword = ref('')
const isActiveFilter = ref<number | ''>('')

const isActiveOptions: SelectOption[] = [
  { label: '全部', value: '' },
  { label: '在职', value: 1 },
  { label: '离职', value: 0 },
]

async function loadVolunteers(): Promise<Volunteer[]> {
  const params: VolunteerQueryParams = {}
  if (searchKeyword.value.trim()) {
    params.name = searchKeyword.value.trim()
  }
  if (isActiveFilter.value !== '') {
    params.is_active = isActiveFilter.value
  }
  return await fetchVolunteers(params)
}

const {
  state: volunteers,
  isLoading,
  error,
  execute: reloadList,
} = useAsyncState(loadVolunteers, [], { immediate: false })

async function reload(): Promise<void> {
  await reloadList()
}

watchDebounced(searchKeyword, () => {
  reloadList()
}, { debounce: 300 })

watch(isActiveFilter, () => {
  reloadList()
})

function resetFilters(): void {
  searchKeyword.value = ''
  isActiveFilter.value = ''
}

const detailVisible = ref(false)
const currentVolunteer = ref<Volunteer | null>(null)

function formatDate(value: string): string {
  try {
    return format(parseISO(value), 'yyyy年M月d日', { locale: zhCN })
  } catch {
    return value
  }
}

function showDetail(volunteer: Volunteer): void {
  currentVolunteer.value = volunteer
  detailVisible.value = true
}

const columns = computed<DataTableColumns<Volunteer>>(() => [
  { title: '姓名', key: 'name', width: 120, ellipsis: { tooltip: true } },
  { title: '联系电话', key: 'phone', width: 140 },
  {
    title: '可服务时段',
    key: 'service_time',
    ellipsis: { tooltip: true },
    render: (row) =>
      row.service_time
        ? h('span', row.service_time)
        : h('span', { class: 'text-muted' }, '未填写'),
  },
  {
    title: '擅长协助类别',
    key: 'skill_category',
    width: 180,
    ellipsis: { tooltip: true },
    render: (row) =>
      row.skill_category
        ? h('span', { class: 'tag tag--skill' }, row.skill_category)
        : h('span', { class: 'text-muted' }, '未填写'),
  },
  {
    title: '登记日期',
    key: 'register_date',
    width: 130,
    render: (row) => formatDate(row.register_date),
  },
  {
    title: '是否在职',
    key: 'is_active',
    width: 100,
    render: (row) =>
      row.is_active
        ? h('span', { class: 'tag tag--active' }, '在职')
        : h('span', { class: 'tag tag--inactive' }, '离职'),
  },
  {
    title: '操作',
    key: 'actions',
    width: 160,
    render: (row) =>
      h('div', { class: 'actions' }, [
        h(
          NButton,
          {
            size: 'small',
            quaternary: true,
            type: 'primary',
            onClick: (e: MouseEvent) => {
              e.stopPropagation()
              emit('edit', row)
            },
          },
          { default: () => '编辑' },
        ),
        h(
          NButton,
          {
            size: 'small',
            quaternary: true,
            type: 'error',
            onClick: (e: MouseEvent) => {
              e.stopPropagation()
              confirmDelete(row)
            },
          },
          { default: () => '删除' },
        ),
      ]),
  },
])

function confirmDelete(volunteer: Volunteer): void {
  dialog.warning({
    title: '确认删除',
    content: `确定删除志愿者「${volunteer.name}」的记录吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      await deleteVolunteer(volunteer.id)
      emit('deleted')
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
      无法获取志愿者列表，请确认后端服务已启动（端口 6000）。
    </n-alert>

    <n-space style="margin-bottom: 16px" align="center">
      <span class="filter-label">姓名：</span>
      <n-input
        v-model:value="searchKeyword"
        placeholder="请输入姓名关键字"
        clearable
        style="width: 200px"
        size="small"
      />
      <span class="filter-label">在职状态：</span>
      <n-select
        v-model:value="isActiveFilter"
        :options="isActiveOptions"
        style="width: 120px"
        size="small"
      />
      <n-button size="small" @click="resetFilters">重置</n-button>
    </n-space>

    <n-data-table
      :columns="columns"
      :data="volunteers"
      :bordered="false"
      :single-line="false"
      striped
      size="small"
      :pagination="{ pageSize: 10 }"
      :row-props="(row: Volunteer) => ({
        onClick: () => showDetail(row),
        style: 'cursor: pointer;',
      })"
    />

    <n-modal
      v-model:show="detailVisible"
      preset="card"
      title="志愿者详情"
      style="width: 520px"
      :mask-closable="true"
    >
      <n-descriptions v-if="currentVolunteer" :column="1" label-placement="left" bordered label-style="width: 120px">
        <n-descriptions-item label="姓名">
          {{ currentVolunteer.name }}
        </n-descriptions-item>
        <n-descriptions-item label="联系电话">
          {{ currentVolunteer.phone }}
        </n-descriptions-item>
        <n-descriptions-item label="可服务时段">
          {{ currentVolunteer.service_time || '（未填写）' }}
        </n-descriptions-item>
        <n-descriptions-item label="擅长协助类别">
          {{ currentVolunteer.skill_category || '（未填写）' }}
        </n-descriptions-item>
        <n-descriptions-item label="登记日期">
          {{ formatDate(currentVolunteer.register_date) }}
        </n-descriptions-item>
        <n-descriptions-item label="是否在职">
          {{ currentVolunteer.is_active ? '在职' : '离职' }}
        </n-descriptions-item>
      </n-descriptions>
      <template #footer>
        <div class="detail-footer">
          <n-button type="primary" @click="detailVisible = false">关闭</n-button>
        </div>
      </template>
    </n-modal>
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

:deep(.tag--active) {
  background: #e8f5e9;
  color: #2e7d32;
}

:deep(.tag--inactive) {
  background: #ffebee;
  color: #c62828;
}

:deep(.tag--skill) {
  background: #e3f2fd;
  color: #1565c0;
}

:deep(.text-muted) {
  color: #999;
  font-size: 12px;
}

.detail-footer {
  display: flex;
  justify-content: flex-end;
}

.filter-label {
  font-size: 14px;
  color: #666;
}
</style>
