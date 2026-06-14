<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue'
import { useAsyncState, watchDebounced } from '@vueuse/core'
import { format, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import type { SelectOption } from 'naive-ui'
import { NButton, NEmpty, NSpace, NTag, useDialog, useMessage } from 'naive-ui'
import {
  deleteAnnouncement,
  fetchAnnouncements,
  toggleAnnouncementPin,
  type AnnouncementQueryParams,
} from '../api/announcement'
import type { Announcement } from '../types/announcement'

const emit = defineEmits<{
  edit: [announcement: Announcement]
  deleted: []
}>()

const dialog = useDialog()
const message = useMessage()

const searchKeyword = ref('')
const isPinnedFilter = ref<number | ''>('')

const isPinnedOptions: SelectOption[] = [
  { label: '全部', value: '' },
  { label: '置顶', value: 1 },
  { label: '普通', value: 0 },
]

async function loadAnnouncements(): Promise<Announcement[]> {
  const params: AnnouncementQueryParams = {}
  if (searchKeyword.value.trim()) {
    params.title = searchKeyword.value.trim()
  }
  if (isPinnedFilter.value !== '') {
    params.is_pinned = isPinnedFilter.value
  }
  return await fetchAnnouncements(params)
}

const {
  state: announcements,
  isLoading,
  error,
  execute: reloadList,
} = useAsyncState(loadAnnouncements, [], { immediate: false })

async function reload(): Promise<void> {
  await reloadList()
}

watchDebounced(searchKeyword, () => {
  reloadList()
}, { debounce: 300 })

watch(isPinnedFilter, () => {
  reloadList()
})

function resetFilters(): void {
  searchKeyword.value = ''
  isPinnedFilter.value = ''
}

function formatPublishTime(value: string): string {
  try {
    return format(parseISO(value), 'yyyy年M月d日 HH:mm', { locale: zhCN })
  } catch {
    return value
  }
}

const pinnedAnnouncements = computed(() =>
  announcements.value.filter((a) => a.is_pinned),
)
const normalAnnouncements = computed(() =>
  announcements.value.filter((a) => !a.is_pinned),
)

async function handleTogglePin(announcement: Announcement): Promise<void> {
  try {
    await toggleAnnouncementPin(announcement.id)
    message.success(announcement.is_pinned ? '已取消置顶' : '已置顶')
    await reload()
  } catch (e: any) {
    const msg = e?.response?.data?.error || '操作失败，请重试'
    message.error(msg)
  }
}

function confirmDelete(announcement: Announcement): void {
  dialog.warning({
    title: '确认删除',
    content: `确定删除公告「${announcement.title}」吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await deleteAnnouncement(announcement.id)
        emit('deleted')
      } catch (e: any) {
        const msg = e?.response?.data?.error || '删除失败，请重试'
        message.error(msg)
        return false
      }
    },
  })
}

function renderCard(announcement: Announcement) {
  return h(
    'div',
    {
      class: ['announcement-card', announcement.is_pinned ? 'is-pinned' : ''],
      key: announcement.id,
    },
    [
      h('div', { class: 'card-header' }, [
        h('div', { class: 'card-title-row' }, [
          announcement.is_pinned
            ? h(NTag, { type: 'warning', size: 'small', round: true }, { default: () => '置顶' })
            : null,
          h('h3', { class: 'card-title' }, announcement.title),
        ]),
        h(
          NSpace,
          { size: 'small', align: 'center' },
          () => [
            h(NButton, {
              size: 'small',
              quaternary: true,
              type: announcement.is_pinned ? 'default' : 'warning',
              onClick: () => handleTogglePin(announcement),
            }, { default: () => announcement.is_pinned ? '取消置顶' : '置顶' }),
            h(NButton, {
              size: 'small',
              quaternary: true,
              type: 'primary',
              onClick: () => emit('edit', announcement),
            }, { default: () => '编辑' }),
            h(NButton, {
              size: 'small',
              quaternary: true,
              type: 'error',
              onClick: () => confirmDelete(announcement),
            }, { default: () => '删除' }),
          ],
        ),
      ]),
      h('div', { class: 'card-meta' }, [
        h('span', { class: 'meta-item' }, [
          h('span', { class: 'meta-label' }, '发布人：'),
          announcement.publisher_nickname || '（未填写）',
        ]),
        h('span', { class: 'meta-item' }, [
          h('span', { class: 'meta-label' }, '发布时间：'),
          formatPublishTime(announcement.publish_time),
        ]),
      ]),
      h('div', { class: 'card-content' }, announcement.content || '（无内容）'),
    ],
  )
}

onMounted(() => {
  reload()
})

defineExpose({ reload })
</script>

<template>
  <n-spin :show="isLoading">
    <n-alert v-if="error" type="error" title="加载失败" style="margin-bottom: 16px">
      无法获取公告列表，请确认后端服务已启动（端口 6000）。
    </n-alert>

    <n-space style="margin-bottom: 16px" align="center">
      <span class="filter-label">标题关键字：</span>
      <n-input
        v-model:value="searchKeyword"
        placeholder="请输入公告标题关键字"
        clearable
        style="width: 240px"
        size="small"
      />
      <span class="filter-label">置顶状态：</span>
      <n-select
        v-model:value="isPinnedFilter"
        :options="isPinnedOptions"
        style="width: 120px"
        size="small"
      />
      <n-button size="small" @click="resetFilters">重置</n-button>
    </n-space>

    <div v-if="announcements.length === 0" class="empty-wrap">
      <n-empty description="暂无公告数据" />
    </div>

    <div v-else class="announcement-list">
      <template v-if="pinnedAnnouncements.length > 0">
        <div class="section-title">
          <n-tag type="warning" round>置顶公告</n-tag>
          <span class="section-count">共 {{ pinnedAnnouncements.length }} 条</span>
        </div>
        <div class="cards-wrap">
          <div v-for="item in pinnedAnnouncements" :key="'pinned-' + item.id">
            <component :is="renderCard(item)" />
          </div>
        </div>
      </template>

      <template v-if="normalAnnouncements.length > 0">
        <div v-if="pinnedAnnouncements.length > 0" class="section-divider" />
        <div class="section-title">
          <n-tag type="info" round>普通公告</n-tag>
          <span class="section-count">共 {{ normalAnnouncements.length }} 条</span>
        </div>
        <div class="cards-wrap">
          <div v-for="item in normalAnnouncements" :key="'normal-' + item.id">
            <component :is="renderCard(item)" />
          </div>
        </div>
      </template>
    </div>
  </n-spin>
</template>

<style scoped>
.announcement-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.empty-wrap {
  padding: 40px 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0 12px;
}

.section-count {
  font-size: 12px;
  color: #999;
}

.section-divider {
  height: 1px;
  background: #eee;
  margin: 20px 0 8px;
}

.cards-wrap {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.announcement-card {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px 18px;
  background: #fff;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.announcement-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-color: #d9d9d9;
}

.announcement-card.is-pinned {
  border-color: #ffe58f;
  background: #fffbe6;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 10px;
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #262626;
  word-break: break-word;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
  color: #8c8c8c;
  margin-bottom: 10px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
}

.meta-label {
  color: #bfbfbf;
}

.card-content {
  font-size: 14px;
  line-height: 1.7;
  color: #434343;
  white-space: pre-wrap;
  word-break: break-word;
  padding: 12px 14px;
  background: #fafafa;
  border-radius: 6px;
}

.is-pinned .card-content {
  background: #fff7cc;
}

.filter-label {
  font-size: 14px;
  color: #666;
}
</style>
