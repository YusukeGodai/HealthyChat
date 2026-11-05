"""Offline integration checks: python -m unittest test_companion."""
import json
import unittest
from unittest.mock import patch

from app import app, chat_histories
from scenes import SCENES


def response(detected="none"):
    return '[RESPONSE]\n我在听。\n[MONITOR]\n' + json.dumps({"detected": detected, "reason": "测试"})


class CompanionTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        chat_histories.clear()
        self.client.post('/api/config', json={"model_a": {"api_key": "offline-test"}})

    def test_scene_context_and_history(self):
        with patch('app.LLMClient.chat_sync', return_value=response()) as model:
            for scene in SCENES:
                result = self.client.post('/api/chat', json={"message": "你好", "scene": scene})
                self.assertIn('assistant_message', result.get_data(as_text=True))
                self.assertIn(SCENES[scene]['prompt'], model.call_args.args[0][0]['content'])
            self.assertEqual(len(next(iter(chat_histories.values()))), 8)

    def test_sticker_reaches_model_and_clear(self):
        with patch('app.LLMClient.chat_sync', return_value=response()) as model:
            self.client.post('/api/chat', json={"sticker": "hug", "scene": "rain"}).get_data()
            self.assertEqual(model.call_args.args[0][1]['content'], '[发送贴图：抱抱自己]')
        self.client.post('/api/clear')
        self.assertFalse(chat_histories)

    def test_validation_does_not_add_history(self):
        for data in [{"scene": "unknown", "message": "hi"}, {"sticker": "bad"}, {"message": []}, {"scene": []}, {}]:
            self.assertEqual(self.client.post('/api/chat', json=data).status_code, 400)
        self.assertFalse(chat_histories)

    def test_health_routes_preserved_in_scenes(self):
        for detected, payload, event in [
            ('psychological', {"intervention": "suggest", "message_to_user": "建议寻求支持"}, 'intervention'),
            ('psychological', {"intervention": "force", "message_to_user": "需要紧急帮助"}, 'intervention'),
            ('health', {"severity": "minor", "message_to_user": "健康建议"}, 'health_advice'),
        ]:
            with patch('app.LLMClient.chat_sync', side_effect=[response(detected), json.dumps(payload)]):
                result = self.client.post('/api/chat', json={"message": "测试", "scene": "night"}).get_data(as_text=True)
                self.assertIn('event: ' + event, result)
                self.assertIn('event: done', result)

    def test_page_and_local_art(self):
        page = self.client.get('/').get_data(as_text=True)
        for scene in SCENES:
            self.assertIn(SCENES[scene]['name'], page)
            with self.client.get(f'/static/art/{scene}.svg') as result:
                self.assertEqual(result.status_code, 200)
        for sticker in ['hug', 'sticker-tea', 'cheer', 'rest']:
            with self.client.get(f'/static/art/{sticker}.svg') as result:
                self.assertEqual(result.status_code, 200)


if __name__ == '__main__':
    unittest.main()
