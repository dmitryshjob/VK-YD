import configparser
import requests
import json
from tqdm import tqdm

config = configparser.ConfigParser()  # создаём объекта парсера
config.read("settings.ini")  # читаем конфиг

class Vk:

    def info_id(self):
        """ Метод для поиска страницы по id или никнейм для VK 
        и корректного ввода данных """
        global  VK_ID
        url = 'https://api.vk.com/method/users.get'
        params = {'access_token' : TOKEN_VK,'v' : '5.131','user_ids' : VK_ID}
        response = requests.get( url, params).json()['response']

        if len(response) >= 1:
            print(' Найдено совпадение :')
            for i in response:
                first_name = i['first_name']
                last_name = i['last_name']
                vk_id = i['id']
                print (f' Пользователь : {first_name}  {last_name} \n Идентификатор :{vk_id}')

                for z in i:
                    if z in 'deactivated':
                        print('Страница пользователя удалена или заблокирована !!!')
                        VK_ID = input(' Повторный ввод данных :')
                        self.info_id()
                        return VK_ID

                is_closed = i['is_closed']
                if is_closed != False:
                    print('Скрыт профиль пользователя настройками приватности !!!')
                    VK_ID = input(' Повторный ввод данных :')
                    self.info_id()
                    return VK_ID     
            VK_ID =  vk_id  
            return vk_id

        if len(response) == 0:
            print('Неверно введены данные !!!')
            VK_ID = input('Введите Id пользователя или никнейм :')
            self.info_id()
            return VK_ID
  
    def __init__(self):
        """ Метод для получения основных параметров запроса для VK"""      
        self.token = TOKEN_VK
        self.id = self.info_id()
        self.json, self.export_dict = self.photo_parameters()

    def request_vk(self):
        """ Метод отправки запроса для VK """          
        url = 'https://api.vk.com/method/photos.get'        
        params = {
            'access_token' : self.token,
            'v' : '5.131',
            'album_id' : 'profile',
            'owner_id': self.id,
            'extended': 1,
            'photo_sizes': 1,
        }         
        response = requests.get( url, params).json()['response']['items']
        return response

    def photo_parameters(self):
        """Метод для получения параметров фотографий и списка для выгрузки"""
        response = self.request_vk()
        repeat_likes = {}
        list_files= []
        file_name = {}
        count = 0
        for x in response:    
            max_sizes_photo = sorted(x['sizes'], key=lambda x: x['height'])[-1] # максимальный размер фотографий      
            likes = x['likes']['count']
            if likes in repeat_likes:        
                repeat_likes[likes] += 1                    
            else:
                repeat_likes[likes] = 1    
         
            if repeat_likes.get(likes) > 1:
                max_sizes_photo['file_name'] = str(x['date']) + '.jpg'  
                count += 1                   
            else:
                max_sizes_photo['file_name'] = str(x['likes']['count']) + '.jpg'   
                count += 1    

            list_files.append({'file_name':max_sizes_photo['file_name'],'size':max_sizes_photo['type']}) 

            file_name.update({max_sizes_photo['file_name']:max_sizes_photo['url']})
            
   
        print(f'Найдено : {count} фотографий')
        return  list_files, file_name    

    def file_parameters(self):
        """Метод создает файл Json с параметрами фотографий """
        print('Создан файл с параметрами фотографий')
        with open('VK_photo', 'w') as file:  # информация по фотографиям в файле VK_photo
            json.dump(VK.json,file) 


class Yandex:

    host = 'https://cloud-api.yandex.net'
    def info_token(self):
        """Метод для проверки токена на Яндекс диске"""
        global Ya_token
        url = 'https://cloud-api.yandex.net/v1/disk'
        headers = {'Authorization': Ya_token}
        response = requests.get(url, headers = headers)
        if response.status_code != 200:
            print('Токен не найден !!!')
            Ya_token = input('Введите токен :')
            self.info_token()
            return Ya_token
        elif response.status_code == 200:
            return Ya_token
    


    def __init__(self, folder_name, token, num ): # основные параметры для загрузки фотографий
        """ Метод для получения основных параметров запроса для Яндекс диск """  
        self.token = self.info_token()
        self.files_num = num
        self.url = f'{self.host}/v1/disk/resources/upload'
        self.headers = {'Authorization': self.token}
        self.folder = self._create_folder(folder_name)

    def _create_folder(self, folder_name): # создания папки
        """ Метод для получения основных параметров запроса для Яндекс диск """        
        url = f'{self.host}/v1/disk/resources'
        params = {'path': folder_name}
        if requests.get(url, headers=self.headers, params=params).status_code != 200:
            requests.put(url, headers=self.headers, params=params)
            print(f'\nПапка <<<<< {folder_name} >>>>> успешно создана. \n')
        else:
            print(f'\nПапка <<<<< {folder_name} >>>> уже существует !!! \n')    
        return folder_name

    def getting_link(self, folder_name): # получения ссылки для загрузки фотографий
        """Метод для получения ссылки для загрузки на Яндекс диск"""
        url = f'{self.host}/v1/disk/resources'
        params = {'path': folder_name}
        resource = requests.get(url, headers=self.headers, params=params).json()['_embedded']['items']
        file_repetition = []        
        for name in resource:
            file_repetition.append(name['name'])    
        return file_repetition

    def uploading_photos(self, dict_files): # загрузка фотографий
        """Метод загрузки фотографий на Яндекс диск"""
        files_in_folder = self.getting_link(self.folder)
        copy_counter = 0        
        for key, i in zip(dict_files.keys(), tqdm(range(self.files_num ))):           
            if copy_counter < self.files_num:
                if key not in files_in_folder:
                    params = {'path': f'{self.folder}/{key}',
                              'url': dict_files[key],
                              'overwrite': 'false'}
                    requests.post(self.url, headers=self.headers, params=params)
                    copy_counter += 1
                else:
                    print(f' Файл {key} уже существует и не будет скопирован !!!')
            else:
                break
        print(f'Новых фотографий скопировано : {copy_counter}')
            
if __name__ == '__main__':
  
    TOKEN_VK = config['token']['Vk_token']
    VK_ID = input('Введите Id пользователя или никнейм :') # Запрос пользователя                                               
    VK = Vk()  # Создаем экземпляр класса VK
    VK.file_parameters() # Создаем файл Json

    while True: # Проверка корректного ввода числа
        try:
            num = int(input('Ввидете число фотографий для загрузки :'))
            break
        except ValueError:
            print('Вы ввели не число !!!')

    Ya_token = input('Введите яндекс токен :') # Запрос пользователя 
    # Ya_token = 'y0_AgAAAABkuGpgAADLWwAAAADRmiQicuZXszXcTha7eRudxeA0jOx_8_Y'
   
    YANDEX = Yandex('Photos from Vk', Ya_token, num) # Создаем экземпляр класса Yandex
    YANDEX.uploading_photos(VK.export_dict)  # Вызываем функцию для копирования фотографий     











