<script setup lang="ts">
import { ref, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { NButton, NInput, NModal, NTimeline, NTimelineItem } from 'naive-ui'
import { format, parseISO } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { fetchGiftNotes, createGiftNote } from '../api/note'
import type { GiftNote } from '../types/note'

const props = defineProps<{
  show: boolean
  giftId: number | null
  giftItemName: string
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
}>()

const message = useMessage()

const notes = ref<GiftNote[]>([])
const loading = ref(false)
const newContent = ref('')
const submitting = ref(false)

function formatDateTime(value: string): string {
  try {
    return format(parseISO(value), 'yyyy年M月d日 HH:mm', { locale: zhCN })
  } catch {
    return value
  }
}

async function loadNotes(): Promise<void> {
  if (!props.giftId) return
  loading.value = true
  try {
    notes.value = await fetchGiftNotes(props.giftId)
  } catch {
    message.error('加载备注失败')
  } finally {
    loading.value = false
  }
}

async function handleSubmit(): Promise<void> {
  if (!props.giftId || !newContent.value.trim()) {
    message.warning('请输入备注内容')
    return
  }
  submitting.value = true
  try {
    const note = await createGiftNote(props.giftId, newContent.value.trim())
    notes.value.unshift(note)
    newContent.value = ''
    message.success('备注已添加')
  } catch {
    message.error('添加备注失败')
  } finally {
    submitting.value = false
  }
}

function handleClose(): void {
  emit('update:show', false)
}

watch(
  () => props.show,
  (newVal) => {
    if (newVal && props.giftId) {
      loadNotes()
    } else {
      newContent.value = ''
    }
  },
)
</script>

<template>
  <n-modal
    :show="show"
    @update:show="handleClose"
    preset="card"
    :title="`${giftItemName} - 流转备注`"
    style="width: 560px"
    :mask-closable="true"
  >
    <div class="note-container">
      <n-spin :show="loading">
        <div v-if="notes.length === 0 && !loading" class="empty-state">
          暂无备注记录
        </div>
        <n-timeline v-else line-type="dashed">
          <n-timeline-item
            v-for="note in notes"
            :key="note.id"
            :time="formatDateTime(note.created_at)"
            type="info"
          >
            <div class="note-content">{{ note.content }}</div>
          </n-timeline-item>
        </n-timeline>
      </n-spin>

      <div class="note-input-area">
        <n-input
          v-model:value="newContent"
          type="textarea"
          placeholder="输入备注内容..."
          :rows="3"
          @keydown.enter.ctrl="handleSubmit"
        />
        <div class="note-input-footer">
          <span class="hint-text">按 Ctrl + Enter 快速提交</span>
          <n-button
            type="primary"
            :loading="submitting"
            :disabled="!newContent.trim()"
            @click="handleSubmit"
          >
            添加备注
          </n-button>
        </div>
      </div>
    </div>
  </n-modal>
</template>

<style scoped>
.note-container {
  max-height: 480px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #999;
  font-size: 14px;
}

.note-content {
  font-size: 14px;
  line-height: 1.6;
  color: #333;
  white-space: pre-wrap;
  word-break: break-all;
}

.note-input-area {
  border-top: 1px solid #eee;
  padding-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.note-input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hint-text {
  font-size: 12px;
  color: #999;
}
</style>
