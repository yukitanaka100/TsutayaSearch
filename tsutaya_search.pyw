# coding: UTF-8

import socket
import urllib.request

from contextlib import contextmanager

# timeout in seconds
timeout = 120
socket.setdefaulttimeout(timeout)



import requests
import lxml.html
import threading
from time import sleep
import copy

import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel,
                             QHBoxLayout, QVBoxLayout, QLineEdit,
                             QTextEdit, QProgressBar, QGroupBox, QMessageBox)
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore

#import socks

default_test_ISBN = 9784492533871

MAX_THREAD_TSUTAYA = 700

# UserAgent偽装
from fake_useragent import UserAgent
UA = UserAgent()



@contextmanager
def fetch_url(url, max_times=10, sleep_sec=5):
    """
    HTTP通信をしてステータスコード200が返ってこなかった場合、
    一定の回数再試行をします。 一定の回数試しても駄目な場合、
    最後に開いたファイルオブジェクトを返します。
    Args:
        max_times: 最大試行回数
        sleep_sec: 接続失敗時にスリープする秒数
    例:
        with fetch_url('http://www.18th-technote.com/') as f:
            f.read()
    """
    retry_count = 0
    while True:
        f = urllib.request.urlopen(url)
        try:
            retry_count += 1
            if f.getcode() == 200 or retry_count >= max_times:
                # 200が返ってくるか、最大試行回数に到達した場合
                # ファイルオブジェクトをyieldした後にループを抜けます。
                yield f
                break
            time.sleep(sleep_sec)
        except urllib.error.URLError:
            if len(exc.args) > 0 and isinstance(exc.args[0], socket.timeout):
                print('urllibソケットタイムアウトを検出、リトライします。')
        except socket.timeout:
            print('ソケットタイムアウトを検出、リトライします。')
        finally:
            f.close()



# mirai===================================================================
class srch_mirai( QtCore.QThread ):

    sig_text = QtCore.pyqtSignal(str)
    sig_count = QtCore.pyqtSignal(int)
    sig_pbar = QtCore.pyqtSignal(int)
 
    def __init__( self, parent=None ):
        super( srch_mirai, self ).__init__( parent )
        self.stopped    = False
        self.mutex      = QtCore.QMutex()
 
    def setup( self, isbn ):
        self.stoppped = False
        self.ISBN = isbn
 
    def stop( self ):
        with QtCore.QMutexLocker( self.mutex ):
            self.stopped = True
 
    def run( self ):

        list_mirai = [['code', 'name', 'tel', 'stock']]
        
        ### read file
        f = open('./list_mirai.txt',encoding='utf-8')
        lines = f.readlines()
        f.close()

        shop_num = len(lines)

        count = 0

        for line in lines:
                text = line.replace('\n','')
                text = text.replace('\r','')
                text = text.replace('\ufeff','')
                if text != '':
                        list_mirai.append(text.split(','))

        ### start thread
        i = 1
        while i < len(list_mirai):
                target_url = 'https://www.miraiyashoten.co.jp/search/stockAPI/?isbn=' + self.ISBN + '&storecodes=' + list_mirai[i][0]
                threading.Thread(target=get_stock, args=(target_url, list_mirai[i],)).start()
                i = i + 1
                
        i = 1

        percent = 0.0
        while i < len(list_mirai):

                while list_mirai[i][3] == '':
                        sleep(0.1)
                        
                if list_mirai[i][3] != '0':
                        self.sig_text.emit(list_mirai[i][1] + ' ' + list_mirai[i][2] + ' [' + list_mirai[i][3] + ']')

                self.sig_count.emit(i)
                self.sig_pbar.emit(i * 100 / shop_num)

                i = i + 1

        self.stop()


def get_stock(target_url, shop_info):
        html = requests.get(target_url)

        shop_info[3] = html.text.split(':')[1].replace('"', '').replace('}','')
# =============================================================================




# sanseido===================================================================
class srch_sanseido( QtCore.QThread ):

    sig_text = QtCore.pyqtSignal(str)
    sig_count = QtCore.pyqtSignal(int)
    sig_pbar = QtCore.pyqtSignal(int)
 
    def __init__( self, parent=None ):
        super( srch_sanseido, self ).__init__( parent )
        self.stopped    = False
        self.mutex      = QtCore.QMutex()
 
    def setup( self, isbn ):
        self.stoppped = False
        self.ISBN = isbn
 
    def stop( self ):
        with QtCore.QMutexLocker( self.mutex ):
            self.stopped = True
 
    def run( self ):

        shop_list = [['code', 'name', 'tel', 'stock']]
        
        # get data
        html = requests.get('https://www.books-sanseido.jp/booksearch/BookStockList.action?shoshiKubun=1&isbn=' + self.ISBN)

        root = lxml.html.fromstring(html.content)

        sanseido_data = root.cssselect('section > div > table.spec tr td')

        if len(sanseido_data) % 3 != 0:
            print('error:テーブルからデータを取れませんでした。')
            
        else:

            shop_list = [['code', 'name', 'tel', 'stock']]
            j = 0
            tmp_list = ['', '', '', '']

            while j < len(sanseido_data):
                tmp_list[0] = '0000'
                tmp_list[1] = sanseido_data[j].text.replace('\t', '').replace('\n', '').replace('\r', '')
                j = j + 1
                tmp_list[2] = sanseido_data[j].text.replace('\t', '').replace('\n', '').replace('\r', '')
                j = j + 1
                tmp_list[3] = sanseido_data[j].text.replace('\t', '').replace('\n', '').replace('\r', '')
                j = j + 1

                shop_list.append(copy.deepcopy(tmp_list))


        shop_num = len(shop_list) - 1
             
        # display result
        i = 1
        percent = 0.0
        while i < len(shop_list):
                     
                if shop_list[i][3] == '○':
                        self.sig_text.emit(shop_list[i][1] + ' ' + shop_list[i][2] + ' [○]')

                self.sig_count.emit(i)
               
                self.sig_pbar.emit(i * 100 / shop_num)

                i = i + 1

        self.stop()
# =============================================================================




# kinokuniya===================================================================
class srch_kinokuniya( QtCore.QThread ):

    sig_text = QtCore.pyqtSignal(str)
    sig_count = QtCore.pyqtSignal(int)
    sig_pbar = QtCore.pyqtSignal(int)
 
    def __init__( self, parent=None ):
        super( srch_kinokuniya, self ).__init__( parent )
        self.stopped    = False
        self.mutex      = QtCore.QMutex()
 
    def setup( self, isbn ):
        self.stoppped = False
        self.ISBN = isbn
 
    def stop( self ):
        with QtCore.QMutexLocker( self.mutex ):
            self.stopped = True
 
    def run( self ):

        list_kinokuniya = [['code', 'name', 'tel', 'stock']]
        
        ### read file
        f = open('./list_kinokuniya.txt',encoding='utf-8')
        lines = f.readlines()
        f.close()

        shop_num = len(lines)

        count = 0

        for line in lines:
                text = line.replace('\n','')
                text = text.replace('\r','')
                text = text.replace('\ufeff','')
                if text != '':
                        list_kinokuniya.append(text.split(','))

        ### start thread
        i = 1
        while i < len(list_kinokuniya):
                target_url = 'https://www.kinokuniya.co.jp/disp/CKnSfStockSearchStockView.jsp?CAT=01&GOODS_STK_NO=' + self.ISBN + '&MAN_ENTR_CD1=' + list_kinokuniya[i][0]
                threading.Thread(target=get_stock_kinokuniya, args=(target_url, list_kinokuniya[i],)).start()
                i = i + 1
                
        i = 1

        percent = 0.0
        while i < len(list_kinokuniya):

                while list_kinokuniya[i][3] == '':
                        sleep(0.1)
               
                if list_kinokuniya[i][3] != '0':
                        self.sig_text.emit(list_kinokuniya[i][1] + ' ' + list_kinokuniya[i][2] + ' [' + list_kinokuniya[i][3] + ']')

                self.sig_count.emit(i)
                self.sig_pbar.emit(i * 100 / shop_num)

                i = i + 1

        self.stop()


def get_stock_kinokuniya(target_url, shop_info):

        html = requests.get(target_url)

        root = lxml.html.fromstring(html.content)

        kinokuniya_data = root.cssselect('li.address > b')

        if len(kinokuniya_data) != 1:
            QMessageBox.warning("エラー", u"紀伊国屋：テーブルからデータを取得できませんでした。")
        elif '△' in kinokuniya_data[0].text:
            shop_info[3] = '△'
        elif '○' in kinokuniya_data[0].text:
            shop_info[3] = '○'
        elif '×' in kinokuniya_data[0].text:
            shop_info[3] = '0'
        else:
            QMessageBox.warning("エラー", u"紀伊国屋：ページが不正です。取得プログラムをチェックしてください。")

# =============================================================================



# honto.jp=====================================================================
class srch_hontojp( QtCore.QThread ):

    sig_text = QtCore.pyqtSignal(str)
    sig_count = QtCore.pyqtSignal(int)
    sig_pbar = QtCore.pyqtSignal(int)

    sig_text_maruzen = QtCore.pyqtSignal(str)
    sig_count_maruzen = QtCore.pyqtSignal(int)
    sig_pbar_maruzen = QtCore.pyqtSignal(int)

    sig_text_junkudo = QtCore.pyqtSignal(str)
    sig_count_junkudo = QtCore.pyqtSignal(int)
    sig_pbar_junkudo = QtCore.pyqtSignal(int)

    sig_text_booksmore = QtCore.pyqtSignal(str)
    sig_count_booksmore = QtCore.pyqtSignal(int)
    sig_pbar_booksmore = QtCore.pyqtSignal(int)
    
    def __init__( self, parent=None ):
        super( srch_hontojp, self ).__init__( parent )
        self.stopped    = False
        self.mutex      = QtCore.QMutex()
 
    def setup( self, isbn ):
        self.stoppped = False
        self.ISBN = isbn
 
    def stop( self ):
        with QtCore.QMutexLocker( self.mutex ):
            self.stopped = True
 
    def run( self ):

        ### 書籍コード取得ページ読込
  
        html = requests.get('https://honto.jp/netstore/search_10' + str(self.ISBN) + '.html')
                
        root = lxml.html.fromstring(html.content)

        honto_data = root.cssselect('#displayOrder1 > div > div > div > h2 > a')

        #print('1')

        if len(honto_data) > 0:
            #print(honto_data[0].get('href'))
            #print(honto_data[0].get('href').replace('book_', 'store_06'))
            pass
        else:
            print('1-2')
            self.sig_text.emit('書籍コードが見つかりません。')
            self.sig_text_maruzen.emit('書籍コードが見つかりません。')
            self.sig_text_junkudo.emit('書籍コードが見つかりません。')
            self.sig_text_booksmore.emit('書籍コードが見つかりません。')
            return

        ### 在庫ページ読込

        html2 = requests.get(honto_data[0].get('href').replace('book_', 'store_06'))

        root2 = lxml.html.fromstring(html2.content)

        honto_data_stock = root2.cssselect('#anc01 > div > table > tbody > tr > th > span:nth-child(1)')
        honto_data_name = root2.cssselect('#anc01 > div > table > tbody > tr > th > :nth-child(2)')
        honto_data_tel = root2.cssselect('#anc01 > div > table > tbody > tr > td:nth-child(4)')
        honto_data_shop = root2.cssselect('#anc01 > div > table > tbody > tr > td:nth-child(2) > span')

        if (len(honto_data_stock) != len(honto_data_shop)) or (len(honto_data_name) != len(honto_data_tel)):
            print('error in hontojp:ショップデータの要素数が不正です。')

        list_bunkyodo = [['code', 'name', 'tel', 'stock']]
        list_maruzen = [['code', 'name', 'tel', 'stock']]
        list_junkudo = [['code', 'name', 'tel', 'stock']]
        list_booksmore = [['code', 'name', 'tel', 'stock']]
     
        #print(honto_data_stock)

        ### 振り分け
        i = 0
        while i < len(honto_data_stock):

            if honto_data_shop[i].text.replace('\t', '').replace('\n', '').replace('\r', '') == '文教堂':

                tmp_list = ['', '', '', '']

                tmp_list[0] = '0000'
                tmp_list[1] = honto_data_name[i].text.replace('\t', '').replace('\n', '').replace('\r', '')
                
                if honto_data_tel[i].text != None:
                    tmp_list[2] = honto_data_tel[i].text.replace('\t', '').replace('\n', '').replace('\r', '')
                else:
                    tmp_list[2] = '番号なし'

                tmp_list[3] = honto_data_stock[i].text[2:3]
               
                list_bunkyodo.append(copy.deepcopy(tmp_list))

            elif honto_data_shop[i].text.replace('\t', '').replace('\n', '').replace('\r', '') == '丸善':

                tmp_list = ['', '', '', '']

                tmp_list[0] = '0000'
                tmp_list[1] = honto_data_name[i].text.replace('\t', '').replace('\n', '').replace('\r', '')
                
                if honto_data_tel[i].text != None:
                    tmp_list[2] = honto_data_tel[i].text.replace('\t', '').replace('\n', '').replace('\r', '')
                else:
                    tmp_list[2] = '番号なし'

                tmp_list[3] = honto_data_stock[i].text[2:3]
               
                list_maruzen.append(copy.deepcopy(tmp_list))

            elif honto_data_shop[i].text.replace('\t', '').replace('\n', '').replace('\r', '') == 'ジュンク堂':

                tmp_list = ['', '', '', '']

                tmp_list[0] = '0000'
                tmp_list[1] = honto_data_name[i].text.replace('\t', '').replace('\n', '').replace('\r', '')
                
                if honto_data_tel[i].text != None:
                    tmp_list[2] = honto_data_tel[i].text.replace('\t', '').replace('\n', '').replace('\r', '')
                else:
                    tmp_list[2] = '番号なし'
                
                tmp_list[3] = honto_data_stock[i].text[2:3]
            
                list_junkudo.append(copy.deepcopy(tmp_list))

            elif honto_data_shop[i].text.replace('\t', '').replace('\n', '').replace('\r', '') == 'ブックスモア' or honto_data_shop[i].text.replace('\t', '').replace('\n', '').replace('\r', '') == '栄好堂':

                tmp_list = ['', '', '', '']

                tmp_list[0] = '0000'
                tmp_list[1] = honto_data_name[i].text.replace('\t', '').replace('\n', '').replace('\r', '')

                if honto_data_tel[i].text != None:
                    tmp_list[2] = honto_data_tel[i].text.replace('\t', '').replace('\n', '').replace('\r', '')
                else:
                    tmp_list[2] = '番号なし'

                tmp_list[3] = honto_data_stock[i].text[2:3]
               
                list_booksmore.append(copy.deepcopy(tmp_list))

            else:
                print('error in hontojp:ショップリストにヒットしませんでした。')
                #QMessageBox.warning(self, "エラー", u"honto.jp:ショップリストにヒットしませんでした。")
                
            i = i + 1

        ### データ表示処理（文教堂）
        shop_num = len(list_bunkyodo) - 1
        percent = 0.0
        i = 1
        while i < len(list_bunkyodo):

                while list_bunkyodo[i][3] == '':
                        sleep(0.1)
               
                if (list_bunkyodo[i][3] == '○') or (list_bunkyodo[i][3] == '△'):
                        self.sig_text.emit(list_bunkyodo[i][1] + ' ' + list_bunkyodo[i][2] + ' [' + list_bunkyodo[i][3] + ']')

                self.sig_count.emit(i)
                self.sig_pbar.emit(i * 100 / shop_num)

                i = i + 1

        ### データ表示処理（丸善）
        shop_num = len(list_maruzen) - 1
        percent = 0.0
        i = 1
        while i < len(list_maruzen):

                while list_maruzen[i][3] == '':
                        sleep(0.1)
               
                if (list_maruzen[i][3] == '○') or (list_maruzen[i][3] == '△'):
                        self.sig_text_maruzen.emit(list_maruzen[i][1] + ' ' + list_maruzen[i][2] + ' [' + list_maruzen[i][3] + ']')

                self.sig_count_maruzen.emit(i)
                self.sig_pbar_maruzen.emit(i * 100 / shop_num)

                i = i + 1

        ### データ表示処理（ジュンク堂）
        shop_num = len(list_junkudo) - 1
        percent = 0.0
        i = 1
        while i < len(list_junkudo):

                while list_junkudo[i][3] == '':
                        sleep(0.1)
               
                if (list_junkudo[i][3] == '○') or (list_junkudo[i][3] == '△'):
                        self.sig_text_junkudo.emit(list_junkudo[i][1] + ' ' + list_junkudo[i][2] + ' [' + list_junkudo[i][3] + ']')

                self.sig_count_junkudo.emit(i)
                self.sig_pbar_junkudo.emit(i * 100 / shop_num)

                i = i + 1
                
        ### データ表示処理（ブックスモア）
        shop_num = len(list_booksmore) - 1
        percent = 0.0
        i = 1
        while i < len(list_booksmore):

                while list_booksmore[i][3] == '':
                        sleep(0.1)
               
                if (list_booksmore[i][3] == '○') or (list_booksmore[i][3] == '△'):
                        self.sig_text_booksmore.emit(list_booksmore[i][1] + ' ' + list_booksmore[i][2] + ' [' + list_booksmore[i][3] + ']')

                self.sig_count_booksmore.emit(i)
                self.sig_pbar_booksmore.emit(i * 100 / shop_num)

                i = i + 1

                
        self.stop()
# =============================================================================




# libro========================================================================
class srch_libro( QtCore.QThread ):

    sig_text = QtCore.pyqtSignal(str)
    sig_count = QtCore.pyqtSignal(int)
    sig_pbar = QtCore.pyqtSignal(int)

    def __init__( self, parent=None ):
        super( srch_libro, self ).__init__( parent )
        self.stopped    = False
        self.mutex      = QtCore.QMutex()
 
    def setup( self, isbn ):
        self.stoppped = False
        self.ISBN = isbn
 
    def stop( self ):
        with QtCore.QMutexLocker( self.mutex ):
            self.stopped = True
 
    def run( self ):

        list_libro = [['code', 'name', 'tel', 'stock']]

        ### read file
        f = open('./list_libro.txt',encoding='utf-8')
        lines = f.readlines()
        f.close()

        shop_num = len(lines)

        count = 0

        for line in lines:
                text = line.replace('\n','')
                text = text.replace('\r','')
                text = text.replace('\ufeff','')
                if text != '':
                        list_libro.append(text.split(','))
                        if len(list_libro[-1]) < 4:
                            print('error:libro shop=' + list_libro[-1][0] + 'のデータが不正です。')

        ### start thread
        i = 1
        while i < len(list_libro):
                threading.Thread(target=get_stock_libro, args=(self.ISBN, list_libro[i],)).start()
                i = i + 1


        ### データ表示処理
        shop_num = len(list_libro) - 1
        percent = 0.0
        i = 1
        while i < len(list_libro):

                while list_libro[i][3] == '':
                        sleep(0.1)

                #print(str(i) + " " + list_libro[i][0] + " " + list_libro[i][1] + " " + list_libro[i][2] + " " + list_libro[i][3])

               
                if (list_libro[i][3] == '○'):
                        self.sig_text.emit(list_libro[i][1] + ' ' + list_libro[i][2] + ' [' + list_libro[i][3] + ']')

                self.sig_count.emit(i)
                self.sig_pbar.emit(i * 100 / shop_num)

                i = i + 1


        self.stop()



def get_stock_libro(isbn, shop_info):

        payload = {
            'uid': 'yuki.tanaka.lib@gmail.com',
            'pwd': '09415644'
        }

        s = requests.Session()
        s.post('https://www.honyaclub.com/shop/customer/login.aspx', data=payload)

        html = s.get('http://www.honyaclub.com/shop/goods/search.aspx?search=x&keyw=' + str(isbn))

        root = lxml.html.fromstring(html.content)

        libro_data = root.cssselect('#main > form > div > div.result-item > div > div > div > p.item-bt > a')

        if len(libro_data) > 0:
            pass
        else:
            QMessageBox.warning("エラー", u"libro:書籍が見つからないか、何かの読込エラーです。")

        ### 在庫ページ読込

        html2 = s.get('https://www.honyaclub.com/shop/stock/confirm.aspx?shop_id=' + shop_info[0] + '&code=' + libro_data[0].get('href').split('=')[1])

        root2 = lxml.html.fromstring(html2.content)

        libro_data_stock = root2.cssselect('#main > p.mt10.pl10.bold-txt.highlight-txt')


        if len(libro_data_stock) != 1:
            QMessageBox.warning("エラー", u"libro:在庫要素の読込に失敗しました。")
        elif '在庫あり' in libro_data_stock[0].text:
            shop_info[3] = '○'
        elif '在庫なし' in libro_data_stock[0].text:
            shop_info[3] = '×'
        else:
            QMessageBox.warning("エラー", u"libro：在庫情報のあり/なし情報が不正です。取得プログラムをチェックしてください。")

# =============================================================================



# tsutaya========================================================================
class srch_tsutaya( QtCore.QThread ):

    sig_text = QtCore.pyqtSignal(str)
    sig_error_text = QtCore.pyqtSignal(str)
    sig_count = QtCore.pyqtSignal(int)
    sig_pbar = QtCore.pyqtSignal(int)

    def __init__( self, parent=None ):
        super( srch_tsutaya, self ).__init__( parent )
        self.stopped    = False
        self.mutex      = QtCore.QMutex()
 
    def setup( self, isbn, srch_op ):
        self.stoppped = False
        self.ISBN = isbn
        self.SRCH_OP = srch_op

        # TSUTAYA
        self.chk_disp_ts = chk_disp_tsutaya()
        self.chk_disp_ts.sig.connect(self.disp_tsutaya)

    def stop( self ):
        with QtCore.QMutexLocker( self.mutex ):
            self.stopped = True
 
    def run( self ):

        self.list_tsutaya = [['code', 'name', 'tel', 'stock']]

        ### read file
        try:
            f = open('./list_tsutaya.txt', encoding='utf-8')
        except Exception as e:
            print('=== エラー内容 ===')
            print('type:' + str(type(e)))
            print('args:' + str(e.args))
            #print('message:' + e.message)
            print('e自身:' + str(e))
            self.sig_error_text.emit(str(e))
            return
        else:
            lines = f.readlines()
            f.close()

        self.shop_num = len(lines)

        count = 0

        for line in lines:
                text = line.replace('\n','')
                text = text.replace('\r','')
                text = text.replace('\ufeff','')
                if text != '':
                        self.list_tsutaya.append(text.split(','))
                        if len(self.list_tsutaya[-1]) < 4:
                            print('error:TSUTAYA shop=' + self.list_tsutaya[-1][0] + 'のデータが不正です。')

        i = 0
        self.shop_num = len(self.list_tsutaya) - 1

        self.chk_disp_ts.setup(self.list_tsutaya)
        self.chk_disp_ts.start()

        while i < len(self.list_tsutaya) - 1:

                t = get_stock_tsutaya(self.ISBN, self.list_tsutaya[i+1], self.SRCH_OP)
                
                t.start()
              
                i = i + 1

                if len(threading.enumerate()) > MAX_THREAD_TSUTAYA:
                    # main socks (dummy-1) (dummy-2) GUI の5スレッドができる
                    while len(threading.enumerate()) > 5:
                        sleep(1.0)
                        print(len(threading.enumerate()))

                        if len(threading.enumerate()) < 10:
                            main_thread = threading.currentThread()
                            for th in threading.enumerate():
                                if th is main_thread:
                                    continue
                                print(th.getName())

#        while True:
#            sleep(1.0)
#            print(len(threading.enumerate()))

#            main_thread = threading.currentThread()
#            for th in threading.enumerate():
#                if th is main_thread:
#                    continue
#                print(th.getName())

        
        self.stop()
        

    # 表示用スロット
    @QtCore.pyqtSlot(int, int)
    def disp_tsutaya(self, shop_i, flag):
      
        if flag == 1:
            #print(self.list_tsutaya[shop_i][1] + ' ' + self.list_tsutaya[shop_i][2] + ' [' + self.list_tsutaya[shop_i][3] + ']')
            self.sig_text.emit(self.list_tsutaya[shop_i][1] + ' ' + self.list_tsutaya[shop_i][2] + ' [' + self.list_tsutaya[shop_i][3] + ']')
        elif flag == 0:
            pass
        elif flag == -1:
            self.sig_error_text.emit(self.list_tsutaya[shop_i][1] + ' ' + self.list_tsutaya[shop_i][2] + ' error')

        self.sig_count.emit(shop_i)
        self.sig_pbar.emit(shop_i * 100 / self.shop_num)





# 別働の表示用クラス。サーチクラスから独立して表示を行う。
class chk_disp_tsutaya( QtCore.QThread ):

    sig = QtCore.pyqtSignal(int, int)
    
    def __init__( self, parent=None ):
        super( chk_disp_tsutaya, self ).__init__( parent )
        self.stopped    = False
        self.mutex      = QtCore.QMutex()
 
    def setup( self, list_tsutaya1 ):
        self.stoppped = False
        self.list_tsutaya = list_tsutaya1

    def stop( self ):
        with QtCore.QMutexLocker( self.mutex ):
            self.stopped = True
 
    def run( self ):

        ### データ表示処理
        shop_num = len(self.list_tsutaya) - 1
        i = 1
     
        while i < len(self.list_tsutaya):

                while self.list_tsutaya[i][3] == '':
                        sleep(0.1)
                        #print('wait ...')
               
                if self.list_tsutaya[i][3] == '○':
                        self.sig.emit(i, 1)
                elif self.list_tsutaya[i][3] == '×':
                        self.sig.emit(i, 0)
                elif self.list_tsutaya[i][3] == 'error':
                        self.sig.emit(i, -1)

                i += 1

        self.stop()
        



# op : 1=book, 2=CD, 3=DVD/Blu-ray
class get_stock_tsutaya(threading.Thread):

        def __init__( self, isbn1, shop_info1, srch_op1 ):
            threading.Thread.__init__(self)
            self.isbn = isbn1
            self.shop_info = shop_info1
            self.srch_op = srch_op1
     
        def run(self):

            if self.srch_op == 1:
                op = 'sell_book'
            elif self.srch_op == 2:
                op = 'sell_cd'
            elif self.srch_op == 3:
                op = 'sell_dvd'
            else:
                print('TSUTAYA : srch_opが不正です。srch_op = ' + str(self.srch_op))

                
            target_url = 'http://store-tsutaya.tsite.jp/item/' + op + '/' + str(self.isbn) + '.html?storeId=' + self.shop_info[0]
            #print(target_url)

            retry_count = 0
        
            while True:

                try:
                    if retry_count >= 100:
                        print('リトライ数が上限に達しました。')
                        self.shop_info[3] = 'error'
                        break

                    headers = { "User-Agent" :  UA.ie }
                    req = urllib.request.Request(target_url, headers=headers)
                    f = urllib.request.urlopen(req)
                    html = f.read().decode('utf-8')

                    root = lxml.html.fromstring(html)

                    tsutaya_data = root.cssselect('div.state > span')

                except urllib.error.URLError:
                    #print('urllibソケットタイムアウトを検出、リトライします。')
                    print('-', end='')
                    retry_count += 1
                    sleep(1.0)
                except socket.timeout:
                    #print('ソケットタイムアウトを検出、リトライします。')
                    print('.', end='')
                    retry_count += 1
                    sleep(1.0)
                except ConnectionResetError:
                    print('X', end='')
                    retry_count += 1
                    sleep(1.0)
                else:
                    if len(tsutaya_data) != 2:
                        print('TSUTAYA:書店カラムが表示されません。ショップコード：' + self.shop_info[0] + '\n')
                        retry_count += 1

                        if retry_count >= 5:
                            print('書店カラム読込リトライ数が上限に達しました。')
                            self.shop_info[3] = 'error'
                            break

                        sleep(3.0)
                    else:
                        if tsutaya_data[0].text == '［○］':
                            self.shop_info[3] = '○'
                            #print(self.shop_info[1] + '［○］\n')
                        elif tsutaya_data[0].text == '［－］' or tsutaya_data[0].text == '［×］':
                            self.shop_info[3] = '×'
                            #print(self.shop_info[1] + '［×］\n')
                        else:
                            #print('error:' + self.shop_info[0] + ' ' + tsutaya_data[0].text + '\n')
                            #QMessageBox.warning("エラー", u"libro：在庫情報のあり/なし情報が不正です。取得プログラムをチェックしてください。")
                            print('#######################################################')
                            self.shop_info[3] = 'error'

                        f.close()
                        break


# =============================================================================







# GUI setting #########################################################################

# QWidgetを継承したクラスを作る
class MyWidget(QWidget):

        sig_srch = QtCore.pyqtSignal()
        sig_srch2 = QtCore.pyqtSignal()
        sig_srch3 = QtCore.pyqtSignal()
        
        def __init__(self):
                super().__init__()

                self.init_ui() # 初期設定
                
                self.show()
                

        def init_ui(self):
                # 初期設定を行う
                self.setWindowTitle('TSUTAYA Search')

                self.setWindowIcon(QIcon('icon.png'))
                
                self.clip = QApplication.clipboard()
                

                ### Thread処理用インスタンス #####################################
                
                # 未来屋
                self.srch_m = srch_mirai()
                self.srch_m.sig_text.connect(self.update_text)
                self.srch_m.sig_count.connect(self.update_count)
                self.srch_m.sig_pbar.connect(self.update_pbar)
                # 三省堂
                self.srch_s = srch_sanseido()
                self.srch_s.sig_text.connect(self.update_text_sanseido)
                self.srch_s.sig_count.connect(self.update_count_sanseido)
                self.srch_s.sig_pbar.connect(self.update_pbar_sanseido)
                # 紀伊国屋
                self.srch_k = srch_kinokuniya()
                self.srch_k.sig_text.connect(self.update_text_kinokuniya)
                self.srch_k.sig_count.connect(self.update_count_kinokuniya)
                self.srch_k.sig_pbar.connect(self.update_pbar_kinokuniya)
                # 文教堂
                self.srch_h = srch_hontojp()
                self.srch_h.sig_text.connect(self.update_text_bunkyodo)
                self.srch_h.sig_count.connect(self.update_count_bunkyodo)
                self.srch_h.sig_pbar.connect(self.update_pbar_bunkyodo)
                # 丸善
                self.srch_h.sig_text_maruzen.connect(self.update_text_maruzen)
                self.srch_h.sig_count_maruzen.connect(self.update_count_maruzen)
                self.srch_h.sig_pbar_maruzen.connect(self.update_pbar_maruzen)
                # ジュンク堂
                self.srch_h.sig_text_junkudo.connect(self.update_text_junkudo)
                self.srch_h.sig_count_junkudo.connect(self.update_count_junkudo)
                self.srch_h.sig_pbar_junkudo.connect(self.update_pbar_junkudo)
                # ブックスモア
                self.srch_h.sig_text_booksmore.connect(self.update_text_booksmore)
                self.srch_h.sig_count_booksmore.connect(self.update_count_booksmore)
                self.srch_h.sig_pbar_booksmore.connect(self.update_pbar_booksmore)
                # LIBRO
                self.srch_li = srch_libro()
                self.srch_li.sig_text.connect(self.update_text_libro)
                self.srch_li.sig_count.connect(self.update_count_libro)
                self.srch_li.sig_pbar.connect(self.update_pbar_libro)
                # TSUTAYA
                self.srch_ts = srch_tsutaya()
                self.srch_ts.sig_text.connect(self.update_text_tsutaya)
                self.srch_ts.sig_count.connect(self.update_count_tsutaya)
                self.srch_ts.sig_pbar.connect(self.update_pbar_tsutaya)
                self.srch_ts.sig_error_text.connect(self.update_text_error_tsutaya)

                ### 部品作成 #####################################################

                # 検索部
                self.label_ISBN = QLabel('ISBN/JAN')
                self.label_ISBN.setFixedWidth(55)
                self.txt_ISBN = QLineEdit()
                self.txt_ISBN.setFixedWidth(90)
                self.button = QPushButton('本')
                self.button.setFixedWidth(60)
                self.paste_button = QPushButton('本貼検')
                self.paste_button.setFixedWidth(60)

                # CD/DVD(blu-ray)検索部
                self.label_JAN = QLabel('JAN')
                self.label_JAN.setFixedWidth(55)
                self.txt_JAN = QLineEdit()
                self.txt_JAN.setFixedWidth(90)
                self.button_cd = QPushButton('CD')
                self.button_cd.setFixedWidth(60)
                self.button_dvd = QPushButton('DVD')
                self.button_dvd.setFixedWidth(60)

                self.paste_button_cd = QPushButton('CD貼検')
                self.paste_button_cd.setFixedWidth(60)
                self.paste_button_dvd = QPushButton('DVD貼検')
                self.paste_button_dvd.setFixedWidth(60)

                # コネクト設定
                #self.button.clicked.connect(self.srch_li1)
                #self.button.clicked.connect(self.srch_m1)
                #self.button.clicked.connect(self.srch_s1)
                #self.button.clicked.connect(self.srch_k1)
                #self.button.clicked.connect(self.srch_h1)
                self.button.clicked.connect(self.srch_ts1)
                self.button_cd.clicked.connect(self.srch_ts2)
                self.button_dvd.clicked.connect(self.srch_ts3)

                self.paste_button.clicked.connect(self.paste_search)
                self.paste_button_cd.clicked.connect(self.paste_cd_search)
                self.paste_button_dvd.clicked.connect(self.paste_dvd_search)
                #self.sig_srch.connect(self.srch_li1)
                #self.sig_srch.connect(self.srch_m1)
                #self.sig_srch.connect(self.srch_s1)
                #self.sig_srch.connect(self.srch_k1)
                #self.sig_srch.connect(self.srch_h1)
                self.sig_srch.connect(self.srch_ts1)
                self.sig_srch2.connect(self.srch_ts2)
                self.sig_srch3.connect(self.srch_ts3)




                # 未来屋
                self.txt_mirai = QTextEdit()
                self.txt_mirai.setText('')
                self.txt_count = QLineEdit()
                self.txt_count.setFixedWidth(25)
                self.pbar = QProgressBar()
                self.pbar.setValue(0)
                self.copy_button = QPushButton('コピー')
                self.copy_button.setFixedWidth(40)
                self.copy_button.clicked.connect(self.copy_clip)
                self.group_mirai = QGroupBox('未来屋')
                
                # 三省堂
                self.txt_sanseido = QTextEdit()
                self.txt_sanseido.setText('')
                self.txt_count_sanseido = QLineEdit()
                self.txt_count_sanseido.setFixedWidth(25)
                self.pbar_sanseido = QProgressBar()
                self.pbar_sanseido.setValue(0)
                self.copy_button_sanseido = QPushButton('コピー')
                self.copy_button_sanseido.setFixedWidth(40)
                self.copy_button_sanseido.clicked.connect(self.copy_clip_sanseido)
                self.group_sanseido = QGroupBox('三省堂')

                # 紀伊国屋
                self.txt_kinokuniya = QTextEdit()
                self.txt_kinokuniya.setText('')
                self.txt_count_kinokuniya = QLineEdit()
                self.txt_count_kinokuniya.setFixedWidth(25)
                self.pbar_kinokuniya = QProgressBar()
                self.pbar_kinokuniya.setValue(0)
                self.copy_button_kinokuniya = QPushButton('コピー')
                self.copy_button_kinokuniya.setFixedWidth(40)
                self.copy_button_kinokuniya.clicked.connect(self.copy_clip_kinokuniya)
                self.group_kinokuniya = QGroupBox('紀伊国屋')

                # 文教堂
                self.txt_bunkyodo = QTextEdit()
                self.txt_bunkyodo.setText('')
                self.txt_count_bunkyodo = QLineEdit()
                self.txt_count_bunkyodo.setFixedWidth(25)
                self.pbar_bunkyodo = QProgressBar()
                self.pbar_bunkyodo.setValue(0)
                self.copy_button_bunkyodo = QPushButton('コピー')
                self.copy_button_bunkyodo.setFixedWidth(40)
                self.copy_button_bunkyodo.clicked.connect(self.copy_clip_bunkyodo)
                self.group_bunkyodo = QGroupBox('文教堂')
        
                # 丸善
                self.txt_maruzen = QTextEdit()
                self.txt_maruzen.setText('')
                self.txt_count_maruzen = QLineEdit()
                self.txt_count_maruzen.setFixedWidth(25)
                self.pbar_maruzen = QProgressBar()
                self.pbar_maruzen.setValue(0)
                self.copy_button_maruzen = QPushButton('コピー')
                self.copy_button_maruzen.setFixedWidth(40)
                self.copy_button_maruzen.clicked.connect(self.copy_clip_maruzen)
                self.group_maruzen = QGroupBox('丸善')
                
                # ジュンク堂
                self.txt_junkudo = QTextEdit()
                self.txt_junkudo.setText('')
                self.txt_count_junkudo = QLineEdit()
                self.txt_count_junkudo.setFixedWidth(25)
                self.pbar_junkudo = QProgressBar()
                self.pbar_junkudo.setValue(0)
                self.copy_button_junkudo = QPushButton('コピー')
                self.copy_button_junkudo.setFixedWidth(40)
                self.copy_button_junkudo.clicked.connect(self.copy_clip_junkudo)
                self.group_junkudo = QGroupBox('ジュンク堂')

                # ブックスモア
                self.txt_booksmore = QTextEdit()
                self.txt_booksmore.setText('')
                self.txt_count_booksmore = QLineEdit()
                self.txt_count_booksmore.setFixedWidth(25)
                self.pbar_booksmore = QProgressBar()
                self.pbar_booksmore.setValue(0)
                self.copy_button_booksmore = QPushButton('コピー')
                self.copy_button_booksmore.setFixedWidth(40)
                self.copy_button_booksmore.clicked.connect(self.copy_clip_booksmore)
                self.group_booksmore = QGroupBox('ブックスモア＆栄好堂')

                # LIBRO
                self.txt_libro = QTextEdit()
                self.txt_libro.setText('')
                self.txt_count_libro = QLineEdit()
                self.txt_count_libro.setFixedWidth(25)
                self.pbar_libro = QProgressBar()
                self.pbar_libro.setValue(0)
                self.copy_button_libro = QPushButton('コピー')
                self.copy_button_libro.setFixedWidth(40)
                self.copy_button_libro.clicked.connect(self.copy_clip_libro)
                self.group_libro = QGroupBox('LIBRO')

                # TSUTAYA
                self.txt_tsutaya = QTextEdit()
                self.txt_tsutaya.setText('')
                self.txt_count_tsutaya = QLineEdit()
                self.txt_count_tsutaya.setFixedWidth(35)
                self.pbar_tsutaya = QProgressBar()
                self.pbar_tsutaya.setValue(0)
                self.copy_button_tsutaya = QPushButton('コピー')
                self.copy_button_tsutaya.setFixedWidth(40)
                self.copy_button_tsutaya.clicked.connect(self.copy_clip_tsutaya)
                self.txt_error_tsutaya = QTextEdit()
                self.txt_error_tsutaya.setText('')
                self.group_tsutaya = QGroupBox('TSUTAYA')
                
                # 空グループ作成
                self.txt_blank = QTextEdit()
                self.txt_blank.setText('')
                self.txt_count_blank = QLineEdit()
                self.txt_count_blank.setFixedWidth(25)
                self.pbar_blank = QProgressBar()
                self.pbar_blank.setValue(0)
                self.copy_button_blank = QPushButton('コピー')
                self.copy_button_blank.setFixedWidth(40)
                self.group_blank = QGroupBox('（未実装）')
                # 空2グループ作成
                self.txt_blank2 = QTextEdit()
                self.txt_blank2.setText('')
                self.txt_count_blank2 = QLineEdit()
                self.txt_count_blank2.setFixedWidth(25)
                self.pbar_blank2 = QProgressBar()
                self.copy_button_blank2 = QPushButton('コピー')
                self.copy_button_blank2.setFixedWidth(40)
                self.pbar_blank2.setValue(0)
                self.group_blank2 = QGroupBox('（未実装）')
                
                ### レイアウト作成 ###############################################

                # 中規模レイアウト

                v_layout_main = QVBoxLayout()
                h_layout_large_column1 = QHBoxLayout() # 検索
                h_layout_large_column2 = QHBoxLayout() # 下記を収納
                v_layout_large_row1 = QVBoxLayout() # 未来屋、三省堂、紀伊国屋
                v_layout_large_row2 = QVBoxLayout() # 文教堂、丸善、ジュンク堂
                v_layout_large_row3 = QVBoxLayout() # ブックスモア&栄好堂、リブロ
                v_layout_large_row4 = QVBoxLayout() # TSUTAYA

                # 小規模レイアウト
                h_layout_srch = QHBoxLayout()
                h_layout_mirai = QHBoxLayout()
                v_layout_mirai = QVBoxLayout()
                h_layout_sanseido = QHBoxLayout()
                v_layout_sanseido = QVBoxLayout()
                h_layout_kinokuniya = QHBoxLayout()
                v_layout_kinokuniya = QVBoxLayout()
                h_layout_bunkyodo = QHBoxLayout()
                v_layout_bunkyodo = QVBoxLayout()
                h_layout_maruzen = QHBoxLayout()
                v_layout_maruzen = QVBoxLayout()
                h_layout_junkudo = QHBoxLayout()
                v_layout_junkudo = QVBoxLayout()
                h_layout_booksmore = QHBoxLayout()
                v_layout_booksmore = QVBoxLayout()
                h_layout_libro = QHBoxLayout()
                v_layout_libro = QVBoxLayout()
                h_layout_tsutaya = QHBoxLayout()
                v_layout_tsutaya = QVBoxLayout()
                h_layout_blank = QHBoxLayout()
                v_layout_blank = QVBoxLayout()
                h_layout_blank2 = QHBoxLayout()
                v_layout_blank2 = QVBoxLayout()

                ### レイアウトに部品追加 #########################################

                # 検索レイアウト
                h_layout_srch.addWidget(self.label_ISBN)
                h_layout_srch.addWidget(self.txt_ISBN)
                h_layout_srch.addWidget(self.button)
                h_layout_srch.addWidget(self.paste_button)
                h_layout_srch.addStretch(1)
                # CD/DVD(blu-ray)検索レイアウト
                #h_layout_srch.addWidget(self.label_JAN)
                #h_layout_srch.addWidget(self.txt_JAN)
                h_layout_srch.addWidget(self.button_cd)
                h_layout_srch.addWidget(self.paste_button_cd)                
                h_layout_srch.addWidget(self.button_dvd)
                h_layout_srch.addWidget(self.paste_button_dvd)
                #h_layout_srch.addWidget(self.paste_button)
                # 未来屋レイアウト
                h_layout_mirai.addWidget(self.txt_count)
                h_layout_mirai.addWidget(self.pbar)
                h_layout_mirai.addWidget(self.copy_button)
                v_layout_mirai.addLayout(h_layout_mirai)
                v_layout_mirai.addWidget(self.txt_mirai)
                self.group_mirai.setLayout(v_layout_mirai)
                # 三省堂レイアウト
                h_layout_sanseido.addWidget(self.txt_count_sanseido)
                h_layout_sanseido.addWidget(self.pbar_sanseido)
                h_layout_sanseido.addWidget(self.copy_button_sanseido)                
                v_layout_sanseido.addLayout(h_layout_sanseido)
                v_layout_sanseido.addWidget(self.txt_sanseido)
                self.group_sanseido.setLayout(v_layout_sanseido)
                # 紀伊国屋レイアウト
                h_layout_kinokuniya.addWidget(self.txt_count_kinokuniya)
                h_layout_kinokuniya.addWidget(self.pbar_kinokuniya)
                h_layout_kinokuniya.addWidget(self.copy_button_kinokuniya)
                v_layout_kinokuniya.addLayout(h_layout_kinokuniya)
                v_layout_kinokuniya.addWidget(self.txt_kinokuniya)
                self.group_kinokuniya.setLayout(v_layout_kinokuniya)
                # 文教堂レイアウト
                h_layout_bunkyodo.addWidget(self.txt_count_bunkyodo)
                h_layout_bunkyodo.addWidget(self.pbar_bunkyodo)
                h_layout_bunkyodo.addWidget(self.copy_button_bunkyodo)
                v_layout_bunkyodo.addLayout(h_layout_bunkyodo)
                v_layout_bunkyodo.addWidget(self.txt_bunkyodo)
                self.group_bunkyodo.setLayout(v_layout_bunkyodo)
                # 丸善レイアウト
                h_layout_maruzen.addWidget(self.txt_count_maruzen)
                h_layout_maruzen.addWidget(self.pbar_maruzen)
                h_layout_maruzen.addWidget(self.copy_button_maruzen)
                v_layout_maruzen.addLayout(h_layout_maruzen)
                v_layout_maruzen.addWidget(self.txt_maruzen)
                self.group_maruzen.setLayout(v_layout_maruzen)
                # ジュンク堂レイアウト
                h_layout_junkudo.addWidget(self.txt_count_junkudo)
                h_layout_junkudo.addWidget(self.pbar_junkudo)
                h_layout_junkudo.addWidget(self.copy_button_junkudo)
                v_layout_junkudo.addLayout(h_layout_junkudo)
                v_layout_junkudo.addWidget(self.txt_junkudo)
                self.group_junkudo.setLayout(v_layout_junkudo)
                # ブックスモアレイアウト
                h_layout_booksmore.addWidget(self.txt_count_booksmore)
                h_layout_booksmore.addWidget(self.pbar_booksmore)
                h_layout_booksmore.addWidget(self.copy_button_booksmore)
                v_layout_booksmore.addLayout(h_layout_booksmore)
                v_layout_booksmore.addWidget(self.txt_booksmore)
                self.group_booksmore.setLayout(v_layout_booksmore)
                # LIBROレイアウト
                h_layout_libro.addWidget(self.txt_count_libro)
                h_layout_libro.addWidget(self.pbar_libro)
                h_layout_libro.addWidget(self.copy_button_libro)                
                v_layout_libro.addLayout(h_layout_libro)
                v_layout_libro.addWidget(self.txt_libro)
                self.group_libro.setLayout(v_layout_libro)
                # TSUTAYAレイアウト
                h_layout_tsutaya.addWidget(self.txt_count_tsutaya)
                h_layout_tsutaya.addWidget(self.pbar_tsutaya)
                h_layout_tsutaya.addWidget(self.copy_button_tsutaya)                
                v_layout_tsutaya.addLayout(h_layout_tsutaya)
                v_layout_tsutaya.addWidget(self.txt_tsutaya)
                v_layout_tsutaya.addWidget(self.txt_error_tsutaya)
                self.group_tsutaya.setLayout(v_layout_tsutaya)
                # 空レイアウト
                h_layout_blank.addWidget(self.txt_count_blank)
                h_layout_blank.addWidget(self.pbar_blank)
                h_layout_blank.addWidget(self.copy_button_blank)
                v_layout_blank.addLayout(h_layout_blank)
                v_layout_blank.addWidget(self.txt_blank)
                self.group_blank.setLayout(v_layout_blank)
                # 空2レイアウト
                h_layout_blank2.addWidget(self.txt_count_blank2)
                h_layout_blank2.addWidget(self.pbar_blank2)
                h_layout_blank2.addWidget(self.copy_button_blank2)
                v_layout_blank2.addLayout(h_layout_blank2)
                v_layout_blank2.addWidget(self.txt_blank2)
                self.group_blank2.setLayout(v_layout_blank2)
                
                ### 中規模レイアウトに小規模レイアウトをセット

                h_layout_large_column1.addLayout(h_layout_srch)
                v_layout_large_row1.addWidget(self.group_mirai)
                v_layout_large_row1.addWidget(self.group_sanseido)
                v_layout_large_row1.addWidget(self.group_kinokuniya)
                v_layout_large_row2.addWidget(self.group_bunkyodo)
                v_layout_large_row2.addWidget(self.group_maruzen)
                v_layout_large_row2.addWidget(self.group_junkudo)
                v_layout_large_row3.addWidget(self.group_booksmore)
                v_layout_large_row3.addWidget(self.group_libro)
                v_layout_large_row3.addWidget(self.group_blank)
                #v_layout_large_row3.addWidget(self.group_blank2)
                v_layout_large_row4.addWidget(self.group_tsutaya)

                #h_layout_large_column2.addLayout(v_layout_large_row1)
                #h_layout_large_column2.addLayout(v_layout_large_row2)
                #h_layout_large_column2.addLayout(v_layout_large_row3)
                h_layout_large_column2.addLayout(v_layout_large_row4)
                v_layout_main.addLayout(h_layout_large_column1)
                v_layout_main.addLayout(h_layout_large_column2)

                ### デフォルト情報セット

                self.txt_ISBN.setText(str(default_test_ISBN))
                self.txt_mirai.append('（注意）石巻, 大阪ﾄﾞｰﾑｼﾃｨ,鹿児島,沖縄ﾗｲｶﾑのみの場合は、海外文庫で処理された可能性が高いため、除外すること')
                

                ### レイアウトをセット ############################################
                
                self.setLayout(v_layout_main)
        
                self.show()

                ###################################################################

        # 検索スロット
        @QtCore.pyqtSlot()
        def paste_search(self):
            self.txt_ISBN.setText(self.clip.text())
            self.sig_srch.emit()

        @QtCore.pyqtSlot()
        def paste_cd_search(self):
            self.txt_ISBN.setText(self.clip.text())
            self.sig_srch2.emit()

        @QtCore.pyqtSlot()
        def paste_dvd_search(self):
            self.txt_ISBN.setText(self.clip.text())
            self.sig_srch3.emit()
                

        # 未来屋スロット
        @QtCore.pyqtSlot()
        def srch_m1(self):
                if len(self.txt_ISBN.text()) == 13:
                        self.txt_mirai.setText('')
                        self.update_count(0)
                        self.update_pbar(0)
                        self.srch_m.setup(self.txt_ISBN.text())
                        self.srch_m.start()
                else:
                    QMessageBox.warning(self, "エラー", u"13桁で入力してください。")

        @QtCore.pyqtSlot(str)
        def update_text(self, text):
                self.txt_mirai.append(text)

        @QtCore.pyqtSlot(int)
        def update_count(self, count):
                self.txt_count.setText(str(count))

        @QtCore.pyqtSlot(int)
        def update_pbar(self, percent):
                self.pbar.setValue(percent)

        @QtCore.pyqtSlot()
        def copy_clip(self):
                self.clip.setText(self.txt_mirai.toPlainText())
                QMessageBox.information(self, "未来屋", u"クリップボードにコピーしました。")

            

        # 三省堂スロット
        @QtCore.pyqtSlot()
        def srch_s1(self):
                if len(self.txt_ISBN.text()) == 13:
                        self.txt_sanseido.setText('')
                        self.update_count_sanseido(0)
                        self.update_pbar_sanseido(0)
                        self.srch_s.setup(self.txt_ISBN.text())
                        self.srch_s.start()
                else:
                    #QMessageBox.warning(self, "エラー", u"13桁で入力してください。")
                    pass

        @QtCore.pyqtSlot(str)
        def update_text_sanseido(self, text):
                self.txt_sanseido.append(text)

        @QtCore.pyqtSlot(int)
        def update_count_sanseido(self, count):
                self.txt_count_sanseido.setText(str(count))

        @QtCore.pyqtSlot(int)
        def update_pbar_sanseido(self, percent):
                self.pbar_sanseido.setValue(percent)

        @QtCore.pyqtSlot()
        def copy_clip_sanseido(self):
                self.clip.setText(self.txt_sanseido.toPlainText())
                QMessageBox.information(self, "三省堂", u"クリップボードにコピーしました。")



        # 紀伊国屋スロット
        @QtCore.pyqtSlot()
        def srch_k1(self):
                if len(self.txt_ISBN.text()) == 13:
                        self.txt_kinokuniya.setText('')
                        self.update_count_kinokuniya(0)
                        self.update_pbar_kinokuniya(0)
                        self.srch_k.setup(self.txt_ISBN.text())
                        self.srch_k.start()
                else:
                    #QMessageBox.warning(self, "エラー", u"13桁で入力してください。")
                    pass

        @QtCore.pyqtSlot(str)
        def update_text_kinokuniya(self, text):
                self.txt_kinokuniya.append(text)

        @QtCore.pyqtSlot(int)
        def update_count_kinokuniya(self, count):
                self.txt_count_kinokuniya.setText(str(count))

        @QtCore.pyqtSlot(int)
        def update_pbar_kinokuniya(self, percent):
                self.pbar_kinokuniya.setValue(percent)

        @QtCore.pyqtSlot()
        def copy_clip_kinokuniya(self):
                self.clip.setText(self.txt_kinokuniya.toPlainText())
                QMessageBox.information(self, "紀伊国屋", u"クリップボードにコピーしました。")



        # hontojpスロット
        @QtCore.pyqtSlot()
        def srch_h1(self):
                if len(self.txt_ISBN.text()) == 13:

                        self.txt_bunkyodo.setText('')
                        self.update_count_bunkyodo(0)
                        self.update_pbar_bunkyodo(0)

                        self.txt_maruzen.setText('')
                        self.update_count_maruzen(0)
                        self.update_pbar_maruzen(0)
                        
                        self.txt_junkudo.setText('')
                        self.update_count_junkudo(0)
                        self.update_pbar_junkudo(0)
                        
                        self.txt_booksmore.setText('')
                        self.update_count_booksmore(0)
                        self.update_pbar_booksmore(0)

                        self.srch_h.setup(self.txt_ISBN.text())
                        self.srch_h.start()

                        #print('3')
                else:
                    #QMessageBox.warning(self, "エラー", u"13桁で入力してください。")
                    pass

        # （文教堂スロット）
        @QtCore.pyqtSlot(str)
        def update_text_bunkyodo(self, text):
                self.txt_bunkyodo.append(text)

        @QtCore.pyqtSlot(int)
        def update_count_bunkyodo(self, count):
                self.txt_count_bunkyodo.setText(str(count))

        @QtCore.pyqtSlot(int)
        def update_pbar_bunkyodo(self, percent):
                self.pbar_bunkyodo.setValue(percent)

        @QtCore.pyqtSlot()
        def copy_clip_bunkyodo(self):
                self.clip.setText(self.txt_bunkyodo.toPlainText())
                QMessageBox.information(self, "文教堂", u"クリップボードにコピーしました。")


        # （丸善スロット）
        @QtCore.pyqtSlot(str)
        def update_text_maruzen(self, text):
                self.txt_maruzen.append(text)

        @QtCore.pyqtSlot(int)
        def update_count_maruzen(self, count):
                self.txt_count_maruzen.setText(str(count))

        @QtCore.pyqtSlot(int)
        def update_pbar_maruzen(self, percent):
                self.pbar_maruzen.setValue(percent)

        @QtCore.pyqtSlot()
        def copy_clip_maruzen(self):
                self.clip.setText(self.txt_maruzen.toPlainText())
                QMessageBox.information(self, "丸善", u"クリップボードにコピーしました。")


        # （ジュンク堂スロット）
        @QtCore.pyqtSlot(str)
        def update_text_junkudo(self, text):
                self.txt_junkudo.append(text)

        @QtCore.pyqtSlot(int)
        def update_count_junkudo(self, count):
                self.txt_count_junkudo.setText(str(count))

        @QtCore.pyqtSlot(int)
        def update_pbar_junkudo(self, percent):
                self.pbar_junkudo.setValue(percent)

        @QtCore.pyqtSlot()
        def copy_clip_junkudo(self):
                self.clip.setText(self.txt_junkudo.toPlainText())
                QMessageBox.information(self, "ジュンク堂", u"クリップボードにコピーしました。")


        # （ブックスモアスロット）
        @QtCore.pyqtSlot(str)
        def update_text_booksmore(self, text):
                self.txt_booksmore.append(text)

        @QtCore.pyqtSlot(int)
        def update_count_booksmore(self, count):
                self.txt_count_booksmore.setText(str(count))

        @QtCore.pyqtSlot(int)
        def update_pbar_booksmore(self, percent):
                self.pbar_booksmore.setValue(percent)

        @QtCore.pyqtSlot()
        def copy_clip_booksmore(self):
                self.clip.setText(self.txt_booksmore.toPlainText())
                QMessageBox.information(self, "ブックスモア", u"クリップボードにコピーしました。")


        # LIBROスロット
        @QtCore.pyqtSlot()
        def srch_li1(self):
                if len(self.txt_ISBN.text()) == 13:
                        self.txt_libro.setText('')
                        self.update_count_libro(0)
                        self.update_pbar_libro(0)
                        self.srch_li.setup(self.txt_ISBN.text())
                        self.srch_li.start()
                else:
                    #QMessageBox.warning(self, "エラー", u"13桁で入力してください。")
                    pass

        @QtCore.pyqtSlot(str)
        def update_text_libro(self, text):
                self.txt_libro.append(text)

        @QtCore.pyqtSlot(int)
        def update_count_libro(self, count):
                self.txt_count_libro.setText(str(count))

        @QtCore.pyqtSlot(int)
        def update_pbar_libro(self, percent):
                self.pbar_libro.setValue(percent)

        @QtCore.pyqtSlot()
        def copy_clip_libro(self):
                self.clip.setText(self.txt_libro.toPlainText())
                QMessageBox.information(self, "LIBRO", u"クリップボードにコピーしました。")


        # TSUTAYAスロット
        @QtCore.pyqtSlot()
        def srch_ts1(self):
                if len(self.txt_ISBN.text()) == 13:
                        self.txt_tsutaya.setText('')
                        self.txt_error_tsutaya.setText('')
                        self.update_count_tsutaya(0)
                        self.update_pbar_tsutaya(0)
                        self.srch_ts.setup(self.txt_ISBN.text(), 1)
                        self.srch_ts.start()
                else:
                    QMessageBox.warning(self, "エラー", u"13桁で入力してください。")
                    pass

        @QtCore.pyqtSlot()
        def srch_ts2(self):
                if len(self.txt_ISBN.text()) == 13:
                        self.txt_tsutaya.setText('')
                        self.txt_error_tsutaya.setText('')
                        self.update_count_tsutaya(0)
                        self.update_pbar_tsutaya(0)
                        self.srch_ts.setup(self.txt_ISBN.text(), 2)
                        self.srch_ts.start()
                else:
                    QMessageBox.warning(self, "エラー", u"13桁で入力してください。")
                    pass

        @QtCore.pyqtSlot()
        def srch_ts3(self):
                if len(self.txt_ISBN.text()) == 13:
                        self.txt_tsutaya.setText('')
                        self.txt_error_tsutaya.setText('')
                        self.update_count_tsutaya(0)
                        self.update_pbar_tsutaya(0)
                        self.srch_ts.setup(self.txt_ISBN.text(), 3)
                        self.srch_ts.start()
                else:
                    QMessageBox.warning(self, "エラー", u"13桁で入力してください。")
                    pass

        @QtCore.pyqtSlot(str)
        def update_text_tsutaya(self, text):
                self.txt_tsutaya.append(text)

        @QtCore.pyqtSlot(str)
        def update_text_error_tsutaya(self, text):
                self.txt_error_tsutaya.append(text)

        @QtCore.pyqtSlot(int)
        def update_count_tsutaya(self, count):
                self.txt_count_tsutaya.setText(str(count))

        @QtCore.pyqtSlot(int)
        def update_pbar_tsutaya(self, percent):
                self.pbar_tsutaya.setValue(percent)

        @QtCore.pyqtSlot()
        def copy_clip_tsutaya(self):
                self.clip.setText(self.txt_tsutaya.toPlainText())
                QMessageBox.information(self, "TSUTAYA", u"クリップボードにコピーしました。")


############################################################################################






### MAIN ####################################

if __name__ == '__main__':
        app = QApplication(sys.argv)

        window = MyWidget()

        sys.exit(app.exec_())
        
#############################################
