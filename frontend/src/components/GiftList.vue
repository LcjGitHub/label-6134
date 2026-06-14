<script setup lang="ts">
import { computed, h, onMounted, ref, watch } from 'vue'
import { useAsyncState, watchDebounced } from '@vueuse/core'
import { format, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import type { DataTableColumns, SelectOption } from 'naive-ui'
import {
  NButton,
  NDescriptions,
  NDescriptionsItem,
  NInput,
  NModal,
  NSpace,
  useDialog,
  useMessage,
} from 'naive-ui'
import {
  deleteGift,
  exportGifts,
  fetchGifts,
  getVerificationCode,
  markGiftTaken,
  regenerateVerificationCode,
  type GiftQueryParams,
} from '../api/gift'
import type { Gift } from '../types/gift'
import GiftSummaryCards from './GiftSummaryCards.vue'

const emit = defineEmits<{
  edit: [gift: Gift]
  deleted: []
  'view-notes': [gift: Gift]
}>()

const dialog = useDialog()
const message = useMessage()

const summaryRef = ref<InstanceType<typeof GiftSummaryCards> | null>(null)

const searchKeyword = ref('')
const isTakenFilter = ref<number | ''>('')

const isTakenOptions: SelectOption[] = [
  { label: '全部', value: '' },
  { label: '已取走', value: 1 },
  { label: '待取走', value: 0 },
]

async function loadGifts(): Promise<Gift[]> {
  const params: GiftQueryParams = {}
  if (searchKeyword.value.trim()) {
    params.item_name = searchKeyword.value.trim()
  }
  if (isTakenFilter.value !== '') {
    params.is_taken = isTakenFilter.value
  }
  return await fetchGifts(params)
}

const {
  state: gifts,
  isLoading,
  error,
  execute: reloadList,
} = useAsyncState(loadGifts, [], { immediate: false })

async function reload(): Promise<void> {
  await Promise.all([
    reloadList(),
    summaryRef.value?.reload(),
  ])
}

watchDebounced(searchKeyword, () => {
  reloadList()
}, { debounce: 300 })

watch(isTakenFilter, () => {
  reloadList()
})

function resetFilters(): void {
  searchKeyword.value = ''
  isTakenFilter.value = ''
}

const isExporting = ref(false)

function buildExportParams(): GiftQueryParams {
  const params: GiftQueryParams = {}
  if (searchKeyword.value.trim()) {
    params.item_name = searchKeyword.value.trim()
  }
  if (isTakenFilter.value !== '') {
    params.is_taken = isTakenFilter.value
  }
  return params
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function parseBlobError(blob: Blob): Promise<string | null> {
  try {
    const text = await blob.text()
    const parsed = JSON.parse(text)
    return parsed.error || null
  } catch {
    return null
  }
}

async function handleExport(): Promise<void> {
  if (isExporting.value) return
  isExporting.value = true
  try {
    const blob = await exportGifts(buildExportParams())
    const timestamp = format(new Date(), 'yyyyMMdd_HHmmss')
    const filename = `gift_records_${timestamp}.csv`
    triggerDownload(blob, filename)
    message.success('导出成功')
  } catch (e: any) {
    const blobError = e?.response?.data instanceof Blob
      ? await parseBlobError(e.response.data)
      : null
    const msg = blobError || e?.response?.data?.error || '导出失败，请重试'
    message.error(msg)
  } finally {
    isExporting.value = false
  }
}

const detailVisible = ref(false)
const currentGift = ref<Gift | null>(null)

function formatGiftDate(value: string): string {
  try {
    return format(parseISO(value), 'yyyy年M月d日', { locale: zhCN })
  } catch {
    return value
  }
}

function showDetail(gift: Gift): void {
  currentGift.value = gift
  detailVisible.value = true
}

function showNotes(gift: Gift): void {
  emit('view-notes', gift)
}

const codeModalVisible = ref(false)
const codeModalGift = ref<Gift | null>(null)
const currentCode = ref('')
const codeLoading = ref(false)
const regenerateLoading = ref(false)

async function openCodeModal(gift: Gift): Promise<void> {
  codeModalGift.value = gift
  codeModalVisible.value = true
  currentCode.value = ''
  codeLoading.value = true
  try {
    const result = await getVerificationCode(gift.id)
    currentCode.value = result.verification_code
  } catch (e: any) {
    const msg = e?.response?.data?.error || '获取验证码失败'
    message.error(msg)
    codeModalVisible.value = false
  } finally {
    codeLoading.value = false
  }
}

async function handleRegenerateCode(): Promise<void> {
  if (!codeModalGift.value) return
  regenerateLoading.value = true
  try {
    const result = await regenerateVerificationCode(codeModalGift.value.id)
    currentCode.value = result.verification_code
    message.success('验证码已重新生成')
  } catch (e: any) {
    const msg = e?.response?.data?.error || '重新生成失败'
    message.error(msg)
  } finally {
    regenerateLoading.value = false
  }
}

function copyCode(): void {
  if (!currentCode.value) return
  navigator.clipboard.writeText(currentCode.value)
    .then(() => {
      message.success('验证码已复制')
    })
    .catch(() => {
      message.error('复制失败，请手动复制')
    })
}

const markTakenModalVisible = ref(false)
const markTakenGift = ref<Gift | null>(null)
const markTakenCode = ref('')
const markTakenLoading = ref(false)

function openMarkTakenModal(gift: Gift): void {
  markTakenGift.value = gift
  markTakenCode.value = ''
  markTakenModalVisible.value = true
}

async function confirmMarkTakenSubmit(): Promise<void> {
  if (!markTakenGift.value) return
  const code = markTakenCode.value.trim()
  if (!code) {
    message.warning('请输入验证码')
    return
  }
  if (!/^\d{6}$/.test(code)) {
    message.warning('验证码必须是6位数字')
    return
  }

  markTakenLoading.value = true
  try {
    await markGiftTaken(markTakenGift.value.id, code)
    message.success('已标记为取走')
    markTakenModalVisible.value = false
    await reload()
  } catch (e: any) {
    const msg = e?.response?.data?.error || '标记失败，请重试'
    message.error(msg)
  } finally {
    markTakenLoading.value = false
  }
}

const columns = computed<DataTableColumns<Gift>>(() => [
  { title: '物品名', key: 'item_name', width: 140, ellipsis: { tooltip: true } },
  {
    title: '物品类别',
    key: 'category_name',
    width: 110,
    render: (row) =>
      row.category_name
        ? h('span', { class: 'tag tag--category' }, row.category_name)
        : h('span', { class: 'text-muted' }, '未分类'),
  },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  {
    title: '赠送日期',
    key: 'gift_date',
    width: 130,
    render: (row) => formatGiftDate(row.gift_date),
  },
  {
    title: '赠送地点',
    key: 'location',
    width: 110,
    ellipsis: { tooltip: true },
    render: (row) =>
      row.location
        ? h('span', { class: 'tag tag--location' }, row.location)
        : h('span', { class: 'text-muted' }, '未填写'),
  },
  { title: '赠送人昵称', key: 'donor_nickname', width: 130, ellipsis: { tooltip: true } },
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
    width: 380,
    render: (row) =>
      h('div', { class: 'actions' }, [
        !row.is_taken
          ? h(
              NButton,
              {
                size: 'small',
                quaternary: true,
                type: 'success',
                onClick: (e: MouseEvent) => {
                  e.stopPropagation()
                  openMarkTakenModal(row)
                },
              },
              { default: () => '标记已取走' },
            )
          : null,
        !row.is_taken
          ? h(
              NButton,
              {
                size: 'small',
                quaternary: true,
                type: 'warning',
                onClick: (e: MouseEvent) => {
                  e.stopPropagation()
                  openCodeModal(row)
                },
              },
              { default: () => '查看验证码' },
            )
          : null,
        h(
          NButton,
          {
            size: 'small',
            quaternary: true,
            type: 'primary',
            onClick: (e: MouseEvent) => {
              e.stopPropagation()
              showNotes(row)
            },
          },
          { default: () => '查看备注' },
        ),
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
      ].filter(Boolean)),
  },
])

function confirmDelete(gift: Gift): void {
  dialog.warning({
    title: '确认删除',
    content: `确定删除「${gift.item_name}」的赠送记录吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      await deleteGift(gift.id)
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
      无法获取赠送记录，请确认后端服务已启动（端口 6000）。
    </n-alert>

    <GiftSummaryCards ref="summaryRef" />

    <n-space style="margin-bottom: 16px" align="center">
      <span class="filter-label">物品名：</span>
      <n-input
        v-model:value="searchKeyword"
        placeholder="请输入物品名关键字"
        clearable
        style="width: 220px"
        size="small"
      />
      <span class="filter-label">取走状态：</span>
      <n-select
        v-model:value="isTakenFilter"
        :options="isTakenOptions"
        style="width: 140px"
        size="small"
      />
      <n-button size="small" @click="resetFilters">重置</n-button>
      <n-button
        size="small"
        type="primary"
        :loading="isExporting"
        :disabled="isLoading"
        @click="handleExport"
      >
        {{ isExporting ? '导出中...' : '导出表格' }}
      </n-button>
    </n-space>

    <n-data-table
      :columns="columns"
      :data="gifts"
      :bordered="false"
      :single-line="false"
      striped
      size="small"
      :pagination="{ pageSize: 10 }"
      :row-props="(row: Gift) => ({
        onClick: () => showDetail(row),
        style: 'cursor: pointer;',
      })"
    />

    <n-modal
      v-model:show="detailVisible"
      preset="card"
      title="赠送记录详情"
      style="width: 560px"
      :mask-closable="true"
    >
      <n-descriptions v-if="currentGift" :column="1" label-placement="left" bordered label-style="width: 120px">
        <n-descriptions-item label="物品名">
          {{ currentGift.item_name }}
        </n-descriptions-item>
        <n-descriptions-item label="物品类别">
          {{ currentGift.category_name || '未分类' }}
        </n-descriptions-item>
        <n-descriptions-item label="描述">
          {{ currentGift.description || '（无）' }}
        </n-descriptions-item>
        <n-descriptions-item label="赠送日期">
          {{ formatGiftDate(currentGift.gift_date) }}
        </n-descriptions-item>
        <n-descriptions-item label="赠送地点">
          {{ currentGift.location || '（未填写）' }}
        </n-descriptions-item>
        <n-descriptions-item label="赠送人昵称">
          {{ currentGift.donor_nickname || '（未填写）' }}
        </n-descriptions-item>
        <n-descriptions-item label="联系电话">
          {{ currentGift.donor_phone || '（未填写）' }}
        </n-descriptions-item>
        <n-descriptions-item label="接收方昵称">
          {{ currentGift.recipient_nickname || '（未填写）' }}
        </n-descriptions-item>
        <n-descriptions-item label="是否已取走">
          {{ currentGift.is_taken ? '已取走' : '待取走' }}
        </n-descriptions-item>
      </n-descriptions>
      <template #footer>
        <div class="detail-footer">
          <n-button type="primary" @click="detailVisible = false">关闭</n-button>
        </div>
      </template>
    </n-modal>

    <n-modal
      v-model:show="codeModalVisible"
      preset="card"
      title="领取验证码"
      style="width: 420px"
      :mask-closable="true"
    >
      <n-spin :show="codeLoading">
        <div class="code-modal-content">
          <p class="code-tip">请将以下验证码告知领取人，用于核验领取身份。</p>
          <div class="code-display">
            <span class="code-text">{{ currentCode }}</span>
          </div>
          <n-space justify="center" style="margin-top: 16px">
            <n-button type="primary" @click="copyCode">
              复制验证码
            </n-button>
            <n-button :loading="regenerateLoading" @click="handleRegenerateCode">
              重新生成
            </n-button>
          </n-space>
        </div>
      </n-spin>
      <template #footer>
        <div class="detail-footer">
          <n-button @click="codeModalVisible = false">关闭</n-button>
        </div>
      </template>
    </n-modal>

    <n-modal
      v-model:show="markTakenModalVisible"
      preset="card"
      title="标记已取走"
      style="width: 420px"
      :mask-closable="true"
    >
      <div class="mark-taken-content">
        <p>请输入领取人提供的 6 位数字验证码，以完成核验。</p>
        <p v-if="markTakenGift" class="mark-taken-item">
          物品：<strong>{{ markTakenGift.item_name }}</strong>
        </p>
        <n-input
          v-model:value="markTakenCode"
          placeholder="请输入6位数字验证码"
          maxlength="6"
          size="large"
          style="margin-top: 16px; text-align: center; font-size: 20px; letter-spacing: 8px;"
          @keyup.enter="confirmMarkTakenSubmit"
        />
      </div>
      <template #footer>
        <div class="detail-footer">
          <n-button @click="markTakenModalVisible = false">取消</n-button>
          <n-button type="primary" :loading="markTakenLoading" @click="confirmMarkTakenSubmit">
            确认取走
          </n-button>
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

:deep(.tag--done) {
  background: #e8f5e9;
  color: #2e7d32;
}

:deep(.tag--pending) {
  background: #fff3e0;
  color: #ef6c00;
}

:deep(.tag--category) {
  background: #e3f2fd;
  color: #1565c0;
}

:deep(.tag--location) {
  background: #f3e5f5;
  color: #7b1fa2;
}

:deep(.text-muted) {
  color: #999;
  font-size: 12px;
}

.detail-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  color: #666;
}

.code-modal-content {
  text-align: center;
  padding: 12px 0;
}

.code-tip {
  color: #666;
  margin-bottom: 20px;
  font-size: 14px;
}

.code-display {
  background: #f5f5f5;
  border-radius: 8px;
  padding: 20px;
  margin: 0 auto;
  width: fit-content;
}

.code-text {
  font-size: 36px;
  font-weight: bold;
  letter-spacing: 8px;
  color: #18a058;
  font-family: 'Courier New', monospace;
}

.mark-taken-content {
  padding: 8px 0;
}

.mark-taken-content p {
  margin: 8px 0;
  color: #666;
  font-size: 14px;
}

.mark-taken-item {
  font-size: 15px !important;
  color: #333 !important;
}

.mark-taken-item strong {
  color: #18a058;
}
</style>
