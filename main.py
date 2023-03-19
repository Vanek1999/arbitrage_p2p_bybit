#_____Разраб: ento_Vanek_____
#_____Подключение библиотек_____
from time import sleep
from bs4 import BeautifulSoup
from itertools import product
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


#_____Инициализация переменных_____
nameCards = {"51": "Payeer", "62": "Qiwi", "75": "Tinkoff", "274": "ЮMoney", "88": "Yandex.Money"}
keysPayMethods = ["51", "62", "75", "274", "88"]
handles, data, bundle = {}, {}, {}
deposit = 6000
listPayMethods = ["Payeer", "Qiwi", "Tinkoff", "ЮMoney", "Yandex.Money"]
#_____Настройки эмулятора_____
options = Options()
options.binary_location = "/usr/bin/google-chrome"
options.add_argument("--start-maximized")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(options=options, executable_path=r'/chromedriver.exe')

#_____Рассчитываем валидность связки_____
def calk(itemBuy, itemSell) -> dict:
	if (float(itemBuy["limits"][0]) <= deposit and float(itemBuy["limits"][1]) >= deposit and
		float(itemSell["limits"][0]) <= deposit and float(itemSell["limits"][1]) >= deposit):
		return {
		"sum": float(deposit / float(itemBuy["price"]) * float(itemSell["price"])),
		"percent": round((float(deposit / float(itemBuy["price"]) * float(itemSell["price"])) - deposit) / deposit * 100, 3)
		}
	return {"sum": 0, "percent": 0}

#_____Собираем валидные связки_____
def getValidity(PayMethodBuy, PayMethodSell) -> None:
	for itemBuy, itemSell in product(data[PayMethodBuy]["buy"].items(), data[PayMethodSell]["sell"].items()):
		itemBuy[1]["limits"] = [i.replace("\xa0", "").replace("RUB", "").replace(",", "") for i in itemBuy[1]["limits"]]
		itemSell[1]["limits"] = [i.replace("\xa0", "").replace("RUB", "").replace(",", "") for i in itemSell[1]["limits"]]
		spred = calk(itemBuy[1], itemSell[1])
		if (spred["sum"] > deposit):
			bundle[spred["percent"]] = f'User: {itemBuy[0]} -> {itemSell[0]}\nPay method: {PayMethodBuy} -> {PayMethodSell}\n\
Price: {itemBuy[1]["price"]} -> {itemSell[1]["price"]}\nSpred: {spred["percent"]}% Clear sum: {spred["sum"] - deposit} RUB\n'

#_____Распаршиваем страницу_____
def GetBybitData(html) -> dict:
	data = {}
	for item in BeautifulSoup(html, 'lxml').find_all('tr'):
		try:
			data[item.find("div", class_="advertiser-name css-7o12g0 ant-tooltip-custom bds-theme-component-light").text] = {"price": 
				item.find("span", class_="price-amount").text, "limits": str(item.find(lambda tag: tag.name == 'div' and 'RUB' in tag.text
													and '~' in tag.text).text).split("USDT")[1].replace("/\xa0", " ").split("~")}
		except:
			pass

	return data

#_____Ждём подгрузки страницы_____
def WaitloadingBybit() -> str:
	try:
		sleep(3)
		WebDriverWait(driver, 20).until(
			lambda driver: driver.execute_script('return document.readyState') == 'complete'
		)
		return "ok"
	except TimeoutException:
		return "error"

#_____Отдаём данные на проверку валидности_____
def BybitBuySell(NumberPayMethod) -> list:
	data = []
	for handle in handles:
		if (NumberPayMethod in handle):
			driver.switch_to.window(handles[handle])
			data.append(GetBybitData(driver.page_source))
	return data

#_____Устанавливаем обновление страницы_____
def setRefreshData() -> None:
	driver.find_element(By.XPATH, '/html/body/div[3]/div[3]/div[1]/div[3]/div[1]/div[5]/div/div').click()
	sleep(0.7)
	driver.find_element(By.XPATH, '/html/body/div[8]/div/div/div/div[2]/div[1]/div/div/div[2]').click()

#_____Устанавливаем платёжный метод_____
def setPayMethod(typeDeal, handle) -> None:
	driver.switch_to.window(handles[f"https://www.bybit.com/fiat/trade/otc/?actionType={typeDeal}&token=USDT&fiat=RUB&paymentMethod={handle}"])
	driver.find_element(By.XPATH, '//*[@id="modal-root"]/div/div/div[1]/span[2]').click()
	driver.find_element(By.XPATH, '//*[@id="paywayAnchorList"]').click()
	driver.find_element(By.XPATH, "/html/body/div[5]/div/div/div/div/div/div/span[2]/input").send_keys(nameCards[handle])
	driver.find_element(By.XPATH, "/html/body/div[5]/div/div/div/div/ul/li/div/span").click()
	driver.find_element(By.XPATH, "/html/body/div[5]/div/div/div/div/section/button[1]").click()
	setRefreshData()

#_____Сортируем объявления на покупку/продажу_____
def getItems(handle) -> dict:
	data = {}
	item = 0
	for items in BybitBuySell(handle):
		if (item == 0):
			data[nameCards.get(handle)] = {"sell": items}
			item += 1
		else:
			data[nameCards.get(handle)].update({"buy": items})
			item = 0
	return data

#_____Запуск_____
def Start() -> None:
	print("\n\n")
	driver.get(f"http://example.com/")
	for payment in keysPayMethods:
		driver.execute_script(f'window.open("https://www.bybit.com/fiat/trade/otc/?actionType=1&token=USDT&fiat=RUB&paymentMethod={payment}");')
		driver.execute_script(f'window.open("https://www.bybit.com/fiat/trade/otc/?actionType=0&token=USDT&fiat=RUB&paymentMethod={payment}");')
	for handle in driver.window_handles:
		driver.switch_to.window(handle)
		handles[driver.current_url] = handle
	for handle in keysPayMethods:
		setPayMethod("1", handle)
		setPayMethod("0", handle)
		data.update(getItems(handle))
	for PayMethodBuy, PayMethodSell in product(listPayMethods, listPayMethods):
		getValidity(PayMethodBuy, PayMethodSell)
	for item in sorted(bundle, reverse=True):
		print(bundle[item], "\n")
	while 1:
		data.clear()
		for handle in keysPayMethods:
			data.update(getItems(handle))
		for PayMethodBuy, PayMethodSell in product(listPayMethods, listPayMethods):
			getValidity(PayMethodBuy, PayMethodSell)
		for item in sorted(bundle, reverse=True):
			print(bundle[item], "\n")
		bundle.clear()
		sleep(6)
		
if __name__ == '__main__':
	Start()
