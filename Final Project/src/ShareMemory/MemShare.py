import mmap
import numpy as np
from ctypes import *

import os.path
import os
import time
#you need writer you need file id, data
class ShareMemWriter:

    def __init__(self, fid, path, mem_file_size = 128, int_size = 8):
        self.fid = fid

        self.data = None
        self.mm = None
        self.path = path
        self.wbyte = 0
        self.rbyte = 0
        self.dbyte = 0
        self.size = mem_file_size * 8
        self.data_size = 0
        self.mem_file_size = mem_file_size
        self.int_size = int_size

    def calibrate(self):

        self.create_mem_file()
        self.create_mapping()

    def check_mem_exists(self):

        result = os.path.isfile(self.path)

        return result

    def create_mem_file(self):

        if self.check_mem_exists() and os.path.getsize(self.path) >= self.size :

            print("mem file size satisfied")

        else:

            with open(self.path, "w+b") as f:
                st = np.arange(self.mem_file_size).astype(np.double)
                f.write(st)
            print(self.path)
            size = os.path.getsize(self.path)

            print("create file size of ", size)



    def create_mapping(self):

        self.mm = mmap.mmap(self.fid.fileno(), access=mmap.ACCESS_WRITE, length=self.mem_file_size)

    def write_string(self):
        #for test purpose
        self.mm.write(b"hello world")
        self.mm.flush()

    def write_data_header(self):

        #print(self.mm.tell())
        #print("this is size")
        #print(self.size)
        self.mm.seek(0)

        self.mm.write(cast(self.size, POINTER(c_int64)))
        self.mm.write(cast(self.data_size, POINTER(c_int64)))
        self.mm.write(cast(self.wbyte, POINTER(c_int64)))
        self.mm.write(cast(self.rbyte, POINTER(c_int64)))
        self.mm.write(cast(self.dbyte, POINTER(c_int64)))
        #print(self.mm.tell())



    def write_data(self, data):
        #print("pointer is here", self.mm.tell())
        #buffer_data = self.data.astype(np.double)
        buffer_data = data.astype(np.double)
        #print(self.mm.tell())
        #print("data size is ", len(data))
        self.mm.write(buffer_data)
        self.mm.flush()

        return 0

    def reset(self):
        self.mm.seek(0)

    def close(self):
        self.mm.close()



class ShareMemReader:

    def __init__(self, fid, path, int_size = 8):
        self.fid = fid
        self.size = 4
        self.path = path
        self.mm = None
        self.content = None
        self.content_idx = 0
        self.int_size = int_size

    def create_mapping(self):

        self.mm = mmap.mmap(self.fid.fileno(), length=self.size, access=mmap.ACCESS_COPY)
        #self.mm = mmap.mmap(-1, length=, prot=mmap.PROT_WRITE | mmap.PROT_READ)


    def read_data_size(self):

        #print(self.mm.tell())
        self.mm.seek(0)
        temp_cont = self.mm.read(self.int_size)
        data_temp_filesz = cast(temp_cont, POINTER(c_int64))
        #print(self.mm.tell())
        self.size = data_temp_filesz.contents.value
        #print(self.size)
        self.mm.close()
        self.mm = None

        return 0

    def char_2_int(self):
        o_temp = cast(self.content[self.content_idx:self.content_idx + self.int_size], POINTER(c_int64))
        o_value = o_temp.contents.value
        self.content_idx = self.content_idx + self.int_size
        return o_value

    def copy_buffer(self):

        #print("current pos", self.mm.tell())
        self.content = self.mm.read(self.size)
        self.content_idx = 0

    def read_data_header(self):

        data_int = []

        for i in range(5):
            data_int.append(self.char_2_int())

    def read_data_body(self):
        data_buffer = self.content[self.content_idx:len(self.content)]
        #print(len(data_buffer))
        data = np.frombuffer(data_buffer, dtype= np.double, count = 4)
        return data

    def reset(self):
        self.mm.seek(0)

    def close(self):
        self.mm.close()






def main():


    cur_dir = "/".join(os.getcwd().split("/")[0: -1])
    cur_path = os.path.join(cur_dir, "memorymap", "data_visual.txt")
    print(cur_path)
    print(os.getcwd())

    x = input()


    if (x == "w"):

        with open(cur_path, "r+", encoding="UTF-8") as fshare:
            print("write data into memory")
            data = np.array([1000.1,2000.0, -3000.0])

            smw = ShareMemWriter(fshare, cur_path)

            print("start writing --------------------------")
            smw.calibrate()
            tic = time.process_time()
            #smw.write_string()
            smw.write_data_header()
            smw.write_data(data)
            toc = time.process_time()
            #print("time used", 1000*(toc - tic))
            print("writing finished -----------------------")
            input("Press Enter to continue...")

    else:

        with open(cur_path, "r+", encoding="UTF-8") as fshare:
            smr = ShareMemReader(fshare, cur_path)
            print("start reading --------------------------")
            smr.create_mapping()

            smr.read_data_size()

            while(True):

                tic = time.clock()
                smr.create_mapping()
                smr.copy_buffer()
                smr.read_data_header()
                result = smr.read_data_body()
                toc = time.clock()
                print(np.array(result))
                print("time", 1000*(tic - toc))
                smr.reset()
                smr.close()
                time.sleep(0.2)



if __name__ == "__main__":
    main()
