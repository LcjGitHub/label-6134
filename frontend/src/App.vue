<script setup lang="ts">
import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import GiftList from './components/GiftList.vue'
import GiftFormModal from './components/GiftFormModal.vue'
import type { Gift } from './types/gift'

const message = useMessage()
const listRef = ref<InstanceType<typeof GiftList> | null>(null)
const showModal = ref(false)
const editingGift = ref<Gift | null>(null)

/** 打开新建弹窗 */
function handleCreate(): void {
  editingGift.value = null
  showModal.value = true
}

/** 打开编辑弹窗 */
function handleEdit(gift: Gift): void {
  editingGift.value = gift
  showModal.value = true
}

/** 表单提交成功后刷新列表 */
function handleSaved(): void {
  const isEdit = editingGift.value !== null
  showModal.value = false
  listRef.value?.reload()
  message.success(isEdit ? '记录已更新' : '记录已创建')
}

/** 删除成功后刷新列表 */
function handleDeleted(): void {
  listRef.value?.reload()
  message.success('记录已删除')
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>社区旧物赠送流转记录</h1>
        <p class="subtitle">记录社区内旧物赠送与领取情况</p>
      </div>
      <n-button type="primary" @click="handleCreate">新增记录</n-button>
    </header>

    <main class="page-main">
      <GiftList ref="listRef" @edit="handleEdit" @deleted="handleDeleted" />
    </main>

    <GiftFormModal
      v-model:show="showModal"
      :gift="editingGift"
      @saved="handleSaved"
    />
  </div>
</template>

<style scoped>
.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 20px 40px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.page-main {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
</style>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue',
    Arial, 'Noto Sans SC', sans-serif;
  background: #f5f7fa;
  color: #333;
}
</style>
