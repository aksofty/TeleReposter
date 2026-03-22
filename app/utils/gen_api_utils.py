
from datetime import date
import httpx
from loguru import logger

async def gen_api_send(
          message: str, prompt: str, token: str, model: str="gemini-2-5-flash", time_out: float=15.0):
    
    if not all(f.strip() for f in [message, prompt, token]):
         return None
    
    url_endpoint = f"https://api.gen-api.ru/api/v1/networks/{model}"
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    data_input = {
        "is_sync": True,
        "messages": [
            {"role": "user", "content": f"сегодняшняя дата: {date.today().strftime("%d.%m.%Y")}. {prompt} {message}"}
        ]
    }

    logger.info(f"Отправляю на обработку в {model} сообщение: {message[:30]}...")
    response_content = None

    try:
        with httpx.Client(timeout=time_out) as client:
            response = client.post(url_endpoint, json=data_input, headers=headers)
            
            # Проверка на HTTP ошибки (4xx, 5xx)
            response.raise_for_status()
            logger.success(f"Ответ от {model} успешно получен")

            msg_data = response.json()['response'][0]['message'] # type: ignore
            response_content = msg_data.get('content') or ""
            return response_content
        
    except (KeyError, IndexError, TypeError):
        return None
    except httpx.HTTPStatusError as exc:
        logger.error(f"API Error: {exc.response.status_code} - {exc.response.text}")
        return None
    except httpx.TimeoutException:
        logger.error(f"Не дождались ответа от {model} [time-out]")
        return None
    except Exception as e:
        logger.exception(f"Ошибка: {e}")
        return None
