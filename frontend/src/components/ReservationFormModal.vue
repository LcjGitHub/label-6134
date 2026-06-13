<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { format } from 'date-fns'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules, SelectOption } from 'naive-ui'
import { createReservation } from '../api/reservation'
import { fetchGifts } from '../api/gift'
import type { Gift } from '../types/gift'
import type { ReservationFormData } from '../types/reservation'

const props = defineProps<{
  show: boolean
}>()

const emit = defineEmits<{
  'update:show': [value: boolean]
  saved: []
}>()

const message = useMessage()

const formRef = ref<FormInst | null>(null)
const submitting = ref(false)
const gifts = ref<Gift[]>([])
const giftsLoading = ref(false)

const giftOptions = computed<SelectOption[]>(() =>
  gifts.value.map((g) => ({
    label: g.item_name,
    value: g.id,
  })),
)

const defaultForm = (): ReservationFormData => ({
  gift_id: null,
  reserver_nickname: '',
  reserve_time: format(new Date(), 'yyyy-MM-dd HH:mm:ss'),
})

const formModel = ref<ReservationFormData>(defaultForm())

const rules: FormRules = {
  gift_id: [{ required: true, message: '请选择预约物品', trigger: ['blur', 'change'] }],
  reserver_nickname: [{ required: true, message: '请输入预约人昵称', trigger: ['blur', 'input'] }],
  reserve_time: [{ required: true, message: '请选择预约时间', trigger: ['blur', 'change'] }],
}

async function loadGifts(): Promise<void> {
  giftsLoading.value = true
  try {
    gifts.value = await fetchGifts()
  } catch (e: any) {
    const msg = e?.response?.data?.error || '网络异常，物品列表加载失败'
    message.error(msg)
  } finally {
    giftsLoading.value = false
  }
}

watch(
  () => props.show,
  async (visible) => {
    if (!visible) return
    await loadGifts()
    formModel.value = defaultForm()
    formRef.value?.restoreValidation()
  },
  { immediate: true },
)

function handleClose(): void {
  emit('update:show', false)
}

async function handleSubmit(): Promise<void> {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  submitting.value = true
  try {
    await createReservation(formModel.value)
    emit('saved')
    message.success('预约已创建')
  } catch (e: any) {
    const msg = e?.response?.data?.error || '提交失败，请重试'
    message.error(msg)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <n-modal
    :show="show"
    preset="card"
    title="新增预约记录"
    style="width: 520px"
    :mask-closable="false"
    @update:show="emit('update:show', $event)"
  >
    <n-form
      ref="formRef"
      :model="formModel"
      :rules="rules"
      label-placement="left"
      label-width="100"
      require-mark-placement="right-hanging"
    >
      <n-form-item label="预约物品" path="gift_id">
        <n-select
          v-model:value="formModel.gift_id"
          placeholder="请选择物品"
          :options="giftOptions"
          :loading="giftsLoading"
          clearable
        />
      </n-form-item>

      <n-form-item label="预约人昵称" path="reserver_nickname">
        <n-input
          v-model:value="formModel.reserver_nickname"
          placeholder="请输入预约人昵称"
          maxlength="50"
          show-count
        />
      </n-form-item>

      <n-form-item label="预约时间" path="reserve_time">
        <n-date-picker
          v-model:formatted-value="formModel.reserve_time"
          type="datetime"
          format="yyyy-MM-dd HH:mm:ss"
          value-format="yyyy-MM-dd HH:mm:ss"
          placeholder="请选择预约时间"
          style="width: 100%"
          clearable
        />
      </n-form-item>
    </n-form>

    <template #footer>
      <div class="footer">
        <n-button @click="handleClose">取消</n-button>
        <n-button type="primary" :loading="submitting" @click="handleSubmit">
          提交
        </n-button>
      </div>
    </template>
  </n-modal>
</template>

<style scoped>
.footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
