import queue
import threading


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.in_queue = queue.Queue(maxsize)
        self.out_queue = queue.Queue(maxsize)
    
    ##get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the IN queue')
                return pkt_S
            else:
                pkt_S = self.out_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, in_or_out, block=False):
        if in_or_out == 'out':
            # print('putting packet in the OUT queue')
            self.out_queue.put(pkt, block)
        else:
            # print('putting packet in the IN queue')
            self.in_queue.put(pkt, block)
            
        
## Implements a network layer packet.
class NetworkPacket:
    ## packet encoding lengths 
    dst_S_length = 5
    prot_S_length = 1
    
    ##@param dst: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, dst, prot_S, data_S):
        self.dst = dst
        self.data_S = data_S
        self.prot_S = prot_S
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst).zfill(self.dst_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise('%s: unknown prot_S option: %s' %(self, self.prot_S))
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst = byte_S[0 : NetworkPacket.dst_S_length].strip('0')
        prot_S = byte_S[NetworkPacket.dst_S_length : NetworkPacket.dst_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise('%s: unknown prot_S field: %s' %(self, prot_S))
        data_S = byte_S[NetworkPacket.dst_S_length + NetworkPacket.prot_S_length : ]        
        return self(dst, prot_S, data_S)
    

    

## Implements a network host for receiving and transmitting data
class Host:
    
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return self.addr
       
    ## create a packet and enqueue for transmission
    # @param dst: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst, data_S):
        p = NetworkPacket(dst, 'data', data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out') #send packets always enqueued successfully
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router
class Router:
    
    ##@param name: friendly router name for debugging
    # @param cost_D: cost table to neighbors {neighbor: {interface: cost}}
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, cost_D, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.intf_L = [Interface(max_queue_size) for _ in range(len(cost_D))]
        #save neighbors and interfeces on which we connect to them
        self.cost_D = cost_D    # {neighbor: {interface: cost}}
        #TODO: set up the routing table for connected hosts
        if (self.name=='RA'):
            self.rt_tbl_D = {'H1':{'RA': self.cost_D['H1'][0]}, 'RB':{'RA': self.cost_D['RB'][1]}, 'H2':{'RA':100}, 'RA':{'RA':0}, 'RC':{'RA': self.cost_D['RC'][2]}, 'RD':{'RA': 100}}      # {destination: {router: cost}}
            self.rt_tb2_D = {'H1':{'RB': 100}, 'RB':{'RB': 100}, 'H2':{'RB':100}, 'RA':{'RB':100}, 'RC':{'RB': 100}, 'RD':{'RB': 100}}
            self.rt_tb3_D = {'H1':{'RC': 100}, 'RB':{'RC': 100}, 'H2':{'RC':100}, 'RA':{'RC':100}, 'RC':{'RC': 100}, 'RD':{'RC': 100}}      # {destination: {router: cost}}
            self.rt_tb4_D = {'H1':{'RD': 100}, 'RB':{'RD': 100}, 'H2':{'RD':100}, 'RA':{'RD':100}, 'RC':{'RD': 100}, 'RD':{'RD': 100}}
                             
        elif (self.name=='RB'):
            self.rt_tbl_D = {'H1':{'RA': 100}, 'RB':{'RA': 100}, 'H2':{'RA':100}, 'RA':{'RA':100},   'RC':{'RA': 100}, 'RD':{'RA': 100}}      # {destination: {router: cost}}
            self.rt_tb2_D = {'H1':{'RB': 100}, 'RB':{'RB': 0}, 'H2':{'RB':100}, 'RA':{'RB':self.cost_D['RA'][0]}, 'RC':{'RB': 100}, 'RD':{'RB': self.cost_D['RD'][1]}}
            self.rt_tb3_D = {'H1':{'RC': 100}, 'RB':{'RC': 100}, 'H2':{'RC':100}, 'RA':{'RC':100}, 'RC':{'RC': 100}, 'RD':{'RC': 100}}      # {destination: {router: cost}}
            self.rt_tb4_D = {'H1':{'RD': 100}, 'RB':{'RD': 100}, 'H2':{'RD':100}, 'RA':{'RD':100}, 'RC':{'RD': 100}, 'RD':{'RD': 100}}

        elif (self.name=='RC'):
            self.rt_tbl_D = {'H1':{'RA': 100}, 'RB':{'RA': 100}, 'H2':{'RA':100}, 'RA':{'RA':100},   'RC':{'RA': 100}, 'RD':{'RA': 100}}      # {destination: {router: cost}}
            self.rt_tb2_D = {'H1':{'RB': 100}, 'RB':{'RB': 100}, 'H2':{'RB':100}, 'RA':{'RB':100}, 'RC':{'RB': 100}, 'RD':{'RB': 100}}
            self.rt_tb3_D = {'H1':{'RC': 100}, 'RB':{'RC': 100}, 'H2':{'RC':100}, 'RA':{'RC':self.cost_D['RA'][0]}, 'RC':{'RC': 0}, 'RD':{'RC': self.cost_D['RD'][1]}}      # {destination: {router: cost}}
            self.rt_tb4_D = {'H1':{'RD': 100}, 'RB':{'RD': 100}, 'H2':{'RD':100}, 'RA':{'RD':100}, 'RC':{'RD': 100}, 'RD':{'RD': 100}}
        elif (self.name=='RD'):
            self.rt_tbl_D = {'H1':{'RA': 100}, 'RB':{'RA': 100}, 'H2':{'RA':100}, 'RA':{'RA':100},   'RC':{'RA': 100}, 'RD':{'RA': 100}}      # {destination: {router: cost}}
            self.rt_tb2_D = {'H1':{'RB': 100}, 'RB':{'RB': 100}, 'H2':{'RB':100}, 'RA':{'RB':100}, 'RC':{'RB': 100}, 'RD':{'RB': 100}}
            self.rt_tb3_D = {'H1':{'RC': 100}, 'RB':{'RC': 100}, 'H2':{'RC':100}, 'RA':{'RC':100}, 'RC':{'RC': 100}, 'RD':{'RC': 100}}      # {destination: {router: cost}}
            self.rt_tb4_D = {'H1':{'RD': 100}, 'RB':{'RD': self.cost_D['RB'][0]}, 'H2':{'RD':self.cost_D['H2'][2]}, 'RA':{'RD':100}, 'RC':{'RD': self.cost_D['RC'][1]}, 'RD':{'RD': 0}}
            
        print('%s: Initialized routing table' % self)
        
        self.print_routes()
    
        
    ## Print routing table
    def print_routes(self):
        #TODO: print the routes as a two dimensional table
        print(" ______________________________________________________________________")
        print("| %s |" % (self.name), end =" ")
        print("  H1   |", end=" ")
        print("  H2   |", end=" ")
        print("  RA   |", end=" ")
        print("  RB   |", end=" ")
        print("  RC   |", end=" ")
        print("  RD   |")
        print(" ______________________________________________________________________")
        print("| RA |", end =" ")
        print("  %d   |" % self.rt_tbl_D['H1']['RA'], end=" ")
        print("  %d   |" % self.rt_tbl_D['H2']['RA'], end=" ")
        print("  %d   |" % self.rt_tbl_D['RA']['RA'], end=" ")
        print("  %d   |" % self.rt_tbl_D['RB']['RA'], end=" ")
        print("  %d   |" % self.rt_tbl_D['RC']['RA'], end=" ")
        print("  %d   |" % self.rt_tbl_D['RD']['RA'])
        print(" ______________________________________________________________________")
        print("| RB |", end =" ")
        print("  %d   |" % self.rt_tb2_D['H1']['RB'], end=" ")
        print("  %d   |" % self.rt_tb2_D['H2']['RB'], end=" ")
        print("  %d   |" % self.rt_tb2_D['RA']['RB'], end=" ")
        print("  %d   |" % self.rt_tb2_D['RB']['RB'], end=" ")
        print("  %d   |" % self.rt_tb2_D['RC']['RB'], end=" ")
        print("  %d   |" % self.rt_tb2_D['RD']['RB'])
        print(" ______________________________________________________________________")
        print("| RC |", end =" ")
        print("  %d   |" % self.rt_tb3_D['H1']['RC'], end=" ")
        print("  %d   |" % self.rt_tb3_D['H2']['RC'], end=" ")
        print("  %d   |" % self.rt_tb3_D['RA']['RC'], end=" ")
        print("  %d   |" % self.rt_tb3_D['RB']['RC'], end=" ")
        print("  %d   |" % self.rt_tb3_D['RC']['RC'], end=" ")
        print("  %d   |" % self.rt_tb3_D['RD']['RC'])
        print(" ______________________________________________________________________")
        print("| RD |", end =" ")
        print("  %d   |" % self.rt_tb4_D['H1']['RD'], end=" ")
        print("  %d   |" % self.rt_tb4_D['H2']['RD'], end=" ")
        print("  %d   |" % self.rt_tb4_D['RA']['RD'], end=" ")
        print("  %d   |" % self.rt_tb4_D['RB']['RD'], end=" ")
        print("  %d   |" % self.rt_tb4_D['RC']['RD'], end=" ")
        print("  %d   |" % self.rt_tb4_D['RD']['RD'])
        print(" ______________________________________________________________________")


    ## called when printing the object
    def __str__(self):
        return self.name


    ## look through the content of incoming interfaces and 
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            #get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            #if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p,i)
                elif p.prot_S == 'control':
                    self.update_routes(p, i)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))
            


    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            # TODO: Here you will need to implement a lookup into the 
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is 1

            j = list(self.rt_tbl_D.get(str(p.dst)).values())[0]
            if j == 100 and i == 0:
                j = 1
            self.intf_L[j].put(p.to_byte_S(), 'out', True)
            print('%s: forwarding packet "%s" from interface %d to %d' % \
                  (self, p, i, j))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass


    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        # TODO: Send out a routing table update
        #create a routing table update packet
        if self.name=='RA':
            
            for j in range(len(self.rt_tbl_D)): # For all destinations
                n=list(self.rt_tbl_D.keys())[j]
                if (n==self.name):
                    self.rt_tbl_D[n][self.name]=0
                else:
                    self.rt_tbl_D[n][self.name]=100
                
            for j in range(len(self.cost_D)): # For each neighbors
                n=list(self.cost_D.keys())[j]
                interface=list(self.cost_D[n].keys())[0]
                self.rt_tbl_D[n][self.name]=self.cost_D[n][interface]
                
            for j in range(len(self.rt_tbl_D)): # For all destinations
                n=list(self.rt_tbl_D.keys())[j]
                p = NetworkPacket(self.rt_tbl_D[n][self.name], 'control', self.name)
                try:
                    print('%s: sending routing update "%s" from interface %d' % (self, p, i))
                    self.intf_L[i].put(p.to_byte_S(), 'out', True)
                except queue.Full:
                    print('%s: packet "%s" lost on interface %d' % (self, p, i))
                    pass
        elif self.name=='RB':           
            for j in range(len(self.rt_tb2_D)): # For all destinations
                n=list(self.rt_tb2_D.keys())[j]
                if (n==self.name):
                    self.rt_tb2_D[n][self.name]=0
                else:
                    self.rt_tb2_D[n][self.name]=100
                
            for j in range(len(self.cost_D)): # For each neighbors
                n=list(self.cost_D.keys())[j]
                interface=list(self.cost_D[n].keys())[0]
                self.rt_tb2_D[n][self.name]=self.cost_D[n][interface]
                
            for j in range(len(self.rt_tbl_D)): # For all destinations
                n=list(self.rt_tb2_D.keys())[j]
                p = NetworkPacket(self.rt_tb2_D[n][self.name], 'control', self.name)
                try:
                    print('%s: sending routing update "%s" from interface %d' % (self, p, i))
                    self.intf_L[i].put(p.to_byte_S(), 'out', True)
                except queue.Full:
                    print('%s: packet "%s" lost on interface %d' % (self, p, i))
                    pass
        elif self.name=='RC':           
            for j in range(len(self.rt_tb3_D)): # For all destinations
                n=list(self.rt_tb3_D.keys())[j]
                if (n==self.name):
                    self.rt_tb3_D[n][self.name]=0
                else:
                    self.rt_tb3_D[n][self.name]=100
                
            for j in range(len(self.cost_D)): # For each neighbors
                n=list(self.cost_D.keys())[j]
                interface=list(self.cost_D[n].keys())[0]
                self.rt_tb3_D[n][self.name]=self.cost_D[n][interface]
                
            for j in range(len(self.rt_tb3_D)): # For all destinations
                n=list(self.rt_tb3_D.keys())[j]
                p = NetworkPacket(self.rt_tb3_D[n][self.name], 'control', self.name)
                try:
                    print('%s: sending routing update "%s" from interface %d' % (self, p, i))
                    self.intf_L[i].put(p.to_byte_S(), 'out', True)
                except queue.Full:
                    print('%s: packet "%s" lost on interface %d' % (self, p, i))
                    pass
        elif self.name=='RD':           
            for j in range(len(self.rt_tb4_D)): # For all destinations
                n=list(self.rt_tb4_D.keys())[j]
                if (n==self.name):
                    self.rt_tb4_D[n][self.name]=0
                else:
                    self.rt_tb4_D[n][self.name]=100
                
            for j in range(len(self.cost_D)): # For each neighbors
                n=list(self.cost_D.keys())[j]
                interface=list(self.cost_D[n].keys())[0]
                self.rt_tb4_D[n][self.name]=self.cost_D[n][interface]
                
            for j in range(len(self.rt_tb4_D)): # For all destinations
                n=list(self.rt_tb4_D.keys())[j]
                p = NetworkPacket(self.rt_tb4_D[n][self.name], 'control', self.name)
                try:
                    print('%s: sending routing update "%s" from interface %d' % (self, p, i))
                    self.intf_L[i].put(p.to_byte_S(), 'out', True)
                except queue.Full:
                    print('%s: packet "%s" lost on interface %d' % (self, p, i))
                    pass


    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        #TODO: add logic to update the routing tables and
        # possibly send out routing updates
        print('%s: Received routing update %s from interface %d' % (self, p, i))
        while True:
            pkt_S = None
            #get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            #if packet exists make a forwarding decision
            if pkt_S is not None:
                for j in range(len(self.rt_tb2_D)):
                   if (self.name=='RB'):
                       self.rt_tbl_D['RB']['RA']=self.rt_tb2_D['RA']['RB']
                       self.rt_tb3_D['RB']['RC']=self.rt_tb2_D['RC']['RB']
                       self.rt_tb4_D['RB']['RD']=self.rt_tb2_D['RD']['RB']
                       n=list(self.rt_tb2_D.keys())[j]
                       x=self.rt_tb2_D[n]['RB']
                       #if(p.data_S==n):
                       y1=int(p.dst)+self.rt_tb2_D[p.data_S][self.name]
                       self.rt_tb2_D[n]['RB']=min(y1, self.rt_tb2_D[n]['RB'])
                       
                       if (x!=self.rt_tb2_D[n]['RB']):
                           for j in range(len(self.rt_tb2_D)): # For all destinations
                               p = NetworkPacket(self.rt_tb2_D[n][self.name], 'control', self.name)
                               try:
                                   print('%s: sending routing update "%s" from interface %d' % (self, p, i))
                                   self.intf_L[i].put(p.to_byte_S(), 'out', True)
                               except queue.Full:
                                   print('%s: packet "%s" lost on interface %d' % (self, p, i))
                                   pass

                            
                   elif (self.name=='RA'):
                       self.rt_tb2_D['RA']['RB']=self.rt_tbl_D['RB']['RA']
                       self.rt_tb3_D['RA']['RC']=self.rt_tbl_D['RC']['RA']
                       self.rt_tb4_D['RA']['RD']=self.rt_tbl_D['RD']['RA']
                       n=list(self.rt_tbl_D.keys())[j]
                       x=self.rt_tbl_D[n]['RA']
                       y1=int(p.dst)+self.rt_tbl_D[p.data_S][self.name]
                       self.rt_tbl_D[n]['RA']=min(y1, self.rt_tbl_D[n]['RA'])
                       if (x!=self.rt_tbl_D[n]['RA']):
                           for j in range(len(self.rt_tbl_D)): # For all destinations
                                p = NetworkPacket(self.rt_tbl_D[n][self.name], 'control', self.name)
                                try:
                                    print('%s: sending routing update "%s" from interface %d' % (self, p, i))
                                    self.intf_L[i].put(p.to_byte_S(), 'out', True)
                                except queue.Full:
                                    print('%s: packet "%s" lost on interface %d' % (self, p, i))
                                    pass
                                
                   elif (self.name=='RC'):
                       self.rt_tb1_D['RC']['RA']=self.rt_tb3_D['RA']['RC']
                       self.rt_tb2_D['RC']['RB']=self.rt_tb3_D['RB']['RC']
                       self.rt_tb4_D['RC']['RD']=self.rt_tb3_D['RD']['RC']
                       n=list(self.rt_tb3_D.keys())[j]
                       x=self.rt_tb3_D[n]['RC']
                       y1=int(p.dst)+self.rt_tb3_D[p.data_S][self.name]
                       self.rt_tb3_D[n]['RC']=min(y1, self.rt_tb3_D[n]['RC'])
                       if (x!=self.rt_tb3_D[n]['RC']):
                           for j in range(len(self.rt_tb3_D)): # For all destinations
                                p = NetworkPacket(self.rt_tb3_D[n][self.name], 'control', self.name)
                                try:
                                    print('%s: sending routing update "%s" from interface %d' % (self, p, i))
                                    self.intf_L[i].put(p.to_byte_S(), 'out', True)
                                except queue.Full:
                                    print('%s: packet "%s" lost on interface %d' % (self, p, i))
                                    pass
                                
                   elif (self.name=='RD'):
                       self.rt_tb1_D['RD']['RA']=self.rt_tb3_D['RA']['RD']
                       self.rt_tb2_D['RD']['RB']=self.rt_tb3_D['RB']['RD']
                       self.rt_tb3_D['RD']['RC']=self.rt_tb3_D['RC']['RD']
                       n=list(self.rt_tb4_D.keys())[j]
                       x=self.rt_tb4_D[n]['RD']
                       y1=int(p.dst)+self.rt_tb4_D[p.data_S][self.name]
                       self.rt_tb4_D[n]['RD']=min(y1, self.rt_tb4_D[n]['RD'])
                       if (x!=self.rt_tb4_D[n]['RD']):
                           for j in range(len(self.rt_tb4_D)): # For all destinations
                                p = NetworkPacket(self.rt_tb4_D[n][self.name], 'control', self.name)
                                try:
                                    print('%s: sending routing update "%s" from interface %d' % (self, p, i))
                                    self.intf_L[i].put(p.to_byte_S(), 'out', True)
                                except queue.Full:
                                    print('%s: packet "%s" lost on interface %d' % (self, p, i))
                                    pass


            else:
                return
        

                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 
