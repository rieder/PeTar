import collections
import numpy as np
from .base import *
from .data import *

class Core(DictNpArrayMix):
    """ Core of a star cluster
    Keys: (class members)
        time (1D): evolved time of the star cluster
        pos  (2D,3): center of the star cluster
        vel  (2D,3): center velocity of the cluster
        rc   (1D): core radius of the star cluster
    """
    
    def __init__(self, _dat=None, _offset=int(0), _append=False, **kwargs):
        """ DictNpArrayMix type initialzation, see help(DictNpArrayMix.__init__)
        """
        keys  = [['time',1],['pos', 3],['vel', 3], ['rc', 1]]
        DictNpArrayMix.__init__(self, keys, _dat, _offset, _append, **kwargs)

    def calcPotentialCenter(self, single, binary, G):
        """ Calculate potential center of the system and return the result
        r_cm = \sum_i pot_i *r_i /\sum_i pot_i (only count pot_i <0)

        Parameters
        ----------
        single: inhermited SimpleParticle
            Single particle data
        binary: Binary
            Binary particle data
        G: float
            Gravitational constant

        Return
        ----------
        cm_pos: c.m. position, numpy.ndarray with shape (*,3)
        cm_vel: c.m. velocity, numpy.ndarray with shape (*,3)

        """
        pot_s_sel = (single.pot<0)
        pot_s = single.pot[pot_s_sel]
        pos_s = single.pos[pot_s_sel]
        vel_s = single.vel[pot_s_sel]

        binary.calcPot(G)
        pot_b = binary.pot
        pos_b = binary.pos
        vel_b = binary.vel
        
        pot_sum = pot_s.sum() + pot_b.sum()
        cm_pos = np.array([(np.sum(pot_s*pos_s[:,i])+np.sum(pot_b*pos_b[:,i]))/pot_sum for i in range(3)])
        cm_vel = np.array([(np.sum(pot_s*vel_s[:,i])+np.sum(pot_b*vel_b[:,i]))/pot_sum for i in range(3)])

        self.pos = np.append(self.pos,[cm_pos],axis=0)
        self.vel = np.append(self.vel,[cm_vel],axis=0)

        return cm_pos, cm_vel
    
    def calcDensityAndCenter(self, particle, kdtree):
        """ Calculate density based on nearest six neighbors and return the result (Casertano & Hut 1985)
        
        Parameters
        ----------
        particle: inherited SimpleParticle
            Particle data set
        kdtree: scipy.spatial.cKDtree
            3D KDTree of all particle positions, can be generated from findPair

        Return
        ----------
        cm_pos: c.m. position, numpy.ndarray with shape (*,3)
        cm_vel: c.m. velocity, numpy.ndarray with shape (*,3)
        """
        # 6 nearest neighbors
        nb_r_list6, nb_index_list6 = kdtree.query(particle.pos,k=6)
        nb_mass_tot6=np.sum(particle[nb_index_list6].mass,axis=1) + particle.mass
        
        nb_inv_r6 = 1/nb_r_list6[:,5]
        rho = nb_mass_tot6*(nb_inv_r6*nb_inv_r6*nb_inv_r6)
        particle.addNewMember('density',rho)
        rho_tot = rho.sum()
     
        cm_pos = np.array([np.sum(rho*particle.pos[:,i])/rho_tot for i in range(3)])
        cm_vel = np.array([np.sum(rho*particle.vel[:,i])/rho_tot for i in range(3)])
        self.pos = np.append(self.pos, [cm_pos], axis=0)
        self.vel = np.append(self.vel, [cm_vel], axis=0)

        return cm_pos, cm_vel

    def calcCoreRadius(self, particle):
        """ Calculate core radius, using Casertano & Hut (1985) method:
        rc = sqrt(\sum_i rho_i^2 r_i^2 / \sum_i rho_i^2)

        Parameters
        ----------
        particle: inherited SimpleParticle
            Particle data set

        Return
        ----------
        rc: core radius

        """
        rho2 = particle.density*particle.density
        rc = np.sqrt((particle.r2*rho2).sum()/(rho2.sum()))
        self.rc = np.append(self.rc, rc)

        return rc

    def addTime(self, time):
        """ Append a new time to current member 'time'
        """
        self.time = np.append(self.time, time)

class LagrangianVelocity(DictNpArrayMix):
    """ Lagrangian velocity component
        Each velocity member is a 2D numpy.ndarray, the row contain the values corresponding to each Langragian radius and the core radius (last value).
        For example, in default case, mass_fraction array is np.array([0.1, 0.3, 0.5, 0.7, 0.9]). 
        The member 'abs' has the shape (*,6), each row contain the velocity referring to the 0.1, 0.3, 0.5, 0.7, 0.9 of Langragian radii and the core radius (last value).
    
    Keys: (class members)
        abs (2D,n_frac): absolute 3D velocity value
        x   (2D,n_frac): velocity in x axis
        y   (2D,n_frac): velocity in y axis
        z   (2D,n_frac): velocity in z axis
        rad (2D,n_frac): velocity in radial direction
        tan (2D,n_frac): velocity in tangential direction
        rot (2D,n_frac): rotational velocity in x-y plane

        n_frac: number of Lagrangian radii + 1, determined by keyword argument 'mass_fraction'
    """
    
    def __init__(self, _dat=None, _offset=int(0), _append=False, **kwargs):
        """ DictNpArrayMix type initialzation, see help(DictNpArrayMix.__init__)

        Parameters
        ----------
        keyword arguments:
            mass_fraction: an 1D numpy.ndarray to indicate the mass fractions to calculate lagrangian radii.
                           Default is np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        """
        
        m_frac=np.array([0.1,0.3,0.5,0.7,0.9])
        if ('mass_fraction' in kwargs.keys()): m_frac=kwargs['mass_fraction'].copy()
        n_frac = m_frac.size + 1
        keys  = [['abs',n_frac],['x',n_frac],['y',n_frac],['z',n_frac],['rad',n_frac],['tan',n_frac],['rot',n_frac]] # all, x, y, z, radial, tangential, rotational
        DictNpArrayMix.__init__(self, keys, _dat, _offset, _append, **kwargs)
        self.initargs['mass_fraction'] = m_frac

class Lagrangian(DictNpArrayMix):
    """ Lagrangian parameters
    Keys: (class members)
        r (2D,n_frac): Lagrangian radii
        m (2D,n_frac): average mass referring to Lagrangian radii
        n (2D,n_frac): number of particles referring to Lagrangian radii
        vel   (LagrangianVelocity): average velocity referring to Lagrangian radii
        sigma (LagrangianVelocity): velocity dispersion referring to Lagrangian radii
    """

    def __init__(self, _dat=None, _offset=int(0), _append=False, **kwargs):
        """ DictNpArrayMix type initialzation, see help(DictNpArrayMix.__init__)

        Parameters
        ----------
        keyword arguments:
            mass_fraction: an 1D numpy.ndarray to indicate the mass fractions to calculate lagrangian radii.
                           Default is np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        """
        m_frac=np.array([0.1,0.3,0.5,0.7,0.9])
        if ('mass_fraction' in kwargs.keys()): m_frac=kwargs['mass_fraction'].copy()
        n_frac = m_frac.size + 1
        keys = [['r', n_frac],['m', n_frac],['n', n_frac], ['vel', LagrangianVelocity], ['sigma', LagrangianVelocity]]
        DictNpArrayMix.__init__(self, keys, _dat, _offset, _append, **kwargs)
        self.initargs['mass_fraction'] = m_frac

        #keys = [['r', n_frac],['m', n_frac],['n', n_frac]] # radius, mass, number
        #DictNpArrayMix.__init__(self, keys, _dat, _offset, _append, **kwargs)
        #self.vel  = LagrangianVelocity(_dat, _offset+self.ncols, False, **kwargs)
        #self.ncols += self.vel.ncols
        #self.keys.append(['vel',LagrangianVelocity])
        #self.sigma= LagrangianVelocity(_dat, _offset+self.ncols, False, **kwargs)
        #self.ncols += self.sigma.ncols
        #self.keys.append(['sigma',LagrangianVelocity])
        #self.initargs['mass_fraction'] = m_frac

    def calcOneSnapshot(self, _particle, _rc, _mode='sphere'):
        """ Calculate one snapshot lagrangian parameters

        Parameters
        ----------
        _particle: inherited SimpleParticle
            particles data set sorted by distance to the coordinate center
        _rc: float
            core radius
        _mode: string (sphere)
            sphere: calculate averaged properties from center to Lagrangian radii
            shell: calculate properties between two neighbor Lagrangian radii
        """
        shell_mode = True if (_mode == 'shell') else False

        mass_fraction = self.initargs['mass_fraction']
        n_frac = mass_fraction.size+1

        def find_mass_index(_mass_cum,mass_fraction):
            mass_bins=np.append(0,mass_fraction*_mass_cum[-1])
            index,count=np.histogram(_mass_cum,bins=mass_bins)
            index=index.cumsum()
            index[index>=_mass_cum.size]=_mass_cum.size-1
            return index

        if (_particle.size<=1):
            size = self.size
            empty = Lagrangian(np.zeros([1,n_frac*self.ncols]),**self.initargs)
            self.append(empty)
            if (size+1!=self.size):
                raise ValueError('Size should increase one, but increase', self.size-size)
        else:
            self.size += 1
            self.vel.size += 1
            self.sigma.size += 1
            mcum=_particle.mass.cumsum()
            r = np.sqrt(_particle.r2)
            rindex= find_mass_index(mcum, mass_fraction)
            rlagr = r[rindex]
            if(len(self.r.shape)!=2):
                raise ValueError('r shape is wrong',self.r.shape)
            self.r = np.append(self.r, [np.append(rlagr,_rc)], axis=0)
            nlagr = rindex+1
            if (shell_mode): nlagr[1:] -= nlagr[:-1]
            nc = (_particle.r2<(_rc*_rc)).sum()
            self.n = np.append(self.n, [np.append(nlagr,nc)], axis=0)
            mlagr = mcum[rindex]
            if (shell_mode): mlagr[1:] -= mlagr[:-1]
            sel = nlagr>0
            mlagr[sel] /= nlagr[sel]
            if (nc>0): mc = mcum[nc-1]/nc
            else:      mc = 0.0
            self.m = np.append(self.m, [np.append(mlagr,mc)], axis=0)

            m   =_particle.mass 
            vel = _particle.vel
            pos = _particle.pos
            rx = pos[:,0]
            ry = pos[:,1]
            rz = pos[:,2]
            vx = vel[:,0]
            vy = vel[:,1]
            vz = vel[:,2]

            # x-y plane radial velocity * rxy
            rvxy = rx*vx + ry*vy
            # radial velocity value
            vr   = (rvxy + rz*vz)/r
            # tangential velocity vector
            vt = [None]*3
            vt[0] = vx - vr*rx/r
            vt[1] = vy - vr*ry/r
            vt[2] = vz - vr*rz/r
            # x-y plane radial position square
            rxy2 = rx*rx + ry*ry
            # rotational velocity
            vrotx = vx - rvxy*rx/rxy2
            vroty = vy - rvxy*ry/rxy2
            vrot = np.sqrt(vrotx*vrotx+vroty*vroty)
            # rotational direction sign
            vrotd = vrotx*ry - vroty*rx
            ng_sig = (vrotd<0.0)
            vrot[ng_sig] = -vrot[ng_sig]
            
            n_offset = np.append(np.zeros(1),nlagr).astype(int)
            vlst = [vx, vy, vz, vr, vt[0], vt[1], vt[2], vrot]
            vave = [None]*len(vlst)
            for k in range(len(vlst)):
                vlagr = []
                if (shell_mode):
                    vlagr = [np.average(m[n_offset[i]:n_offset[i+1]]*vlst[k][n_offset[i]:n_offset[i+1]])/mlagr[i] if (n_offset[i]<n_offset[i+1]) else 0.0 for i in range(mlagr.size)]
                else:
                    vlagr = [np.average(m[:n_offset[i+1]]*vlst[k][:n_offset[i+1]])/mlagr[i] if (n_offset[i+1]>0) else 0.0 for i in range(mlagr.size)]
                # core radius
                vlagr.append(np.average(m[0:nc]*vlst[k][0:nc])/mc if (nc>0) else 0.0)
                vave[k] = np.array(vlagr)
            
            self.vel.x = np.append(self.vel.x, [vave[0]], axis=0)
            self.vel.y = np.append(self.vel.y, [vave[1]], axis=0)
            self.vel.z = np.append(self.vel.z, [vave[2]], axis=0)
            self.vel.abs= np.append(self.vel.abs, [np.sqrt(vave[0]*vave[0]+vave[1]*vave[1]+vave[2]*vave[2])], axis=0)
            self.vel.rad = np.append(self.vel.rad, [vave[3]], axis=0)
            self.vel.tan = np.append(self.vel.tan, [np.sqrt(vave[4]*vave[4]+vave[5]*vave[5]+vave[6]*vave[6])], axis=0)
            self.vel.rot = np.append(self.vel.rot, [vave[7]], axis=0)
            
            sigma = [None]*len(vlst)
            for k in range(len(vlst)):
                slagr = []
                if (shell_mode):
                    slagr = [np.average(m[n_offset[i]:n_offset[i+1]] * (vlst[k][n_offset[i]:n_offset[i+1]] - vave[k][i])**2) / mlagr[i] if (n_offset[i]<n_offset[i+1]) else 0.0 for i in range(mass_fraction.size)]
                else:
                    slagr = [np.average(m[:n_offset[i+1]] * (vlst[k][:n_offset[i+1]] - vave[k][i])**2) / mlagr[i] if (n_offset[i+1]>0) else 0.0 for i in range(mass_fraction.size)]
                # core radius
                slagr.append(np.average(m[0:nc] * (vlst[k][0:nc] - vave[k][-1])**2) / mc if (nc>0) else 0.0)
                sigma[k] = np.array(slagr)

            self.sigma.x = np.append(self.sigma.x, [np.sqrt(sigma[0])], axis=0)
            self.sigma.y = np.append(self.sigma.y, [np.sqrt(sigma[1])], axis=0)
            self.sigma.z = np.append(self.sigma.z, [np.sqrt(sigma[2])], axis=0)
            self.sigma.abs= np.append(self.sigma.abs, [np.sqrt(sigma[0]+sigma[1]+sigma[2])], axis=0)
            self.sigma.rad = np.append(self.sigma.rad, [np.sqrt(sigma[3])], axis=0)
            self.sigma.tan = np.append(self.sigma.tan, [np.sqrt(sigma[4]+sigma[5]+sigma[6])], axis=0)
            self.sigma.rot = np.append(self.sigma.rot, [np.sqrt(sigma[7])], axis=0)

class LagrangianMultiple(DictNpArrayMix):
    """ Lagrangian for single, binaries and all
    Keys: (class members)
        single (Lagrangian): Lagrangian data for single particles
        binary (Lagrangian): Lagrangian data for binaries
        all (Lagrangian): Lagrangian data for all data (binary is treated as c.m., count once)
    """
    def __init__ (self, _dat=None, _offset=int(0), _append=False, **kwargs):
        """ DictNpArrayMix type initialzation, see help(DictNpArrayMix.__init__)

        Parameters
        ----------
        keyword arguments:
            mass_fraction: an 1D numpy.ndarray to indicate the mass fractions to calculate lagrangian radii.
                               Default is np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        """
        m_frac=np.array([0.1,0.3,0.5,0.7,0.9])
        if ('mass_fraction' in kwargs.keys()): m_frac=kwargs['mass_fraction'].copy()
        keys=[['time',1], ['single',Lagrangian], ['binary', Lagrangian], ['all', Lagrangian]]
        DictNpArrayMix.__init__(self, keys, _dat, _offset, _append, **kwargs)
        self.initargs['mass_fraction'] = m_frac

        #DictNpArrayMix.__init__(self, [['time',1]], _dat, _offset, _append, **kwargs)
        #self.single = Lagrangian(_dat, _offset+self.ncols, False, **kwargs)
        #self.ncols += self.single.ncols
        #self.keys.append(['single',Lagrangian])
        #self.binary = Lagrangian(_dat, _offset+self.ncols, False, **kwargs)
        #self.ncols += self.binary.ncols
        #self.keys.append(['binary',Lagrangian])
        #self.all    = Lagrangian(_dat, _offset+self.ncols, False, **kwargs)
        #self.ncols += self.all.ncols
        #self.keys.append(['all',Lagrangian])
        #self.size = self.all.size


    def calcOneSnapshot(self, time, single, binary, rc, mode):
        """ Calculate Lagrangian radii and related properties for one snapshot

        Parameters
        ----------
        time: float
            current evolved time of the system
        single: inherited SimpleParticle
            single partilces (center is corrected and r2 exist)
        binary: Binary
            binaries (center is corrected and r2 exist)
        mass_fraction: 1D numpy.ndarray
            Lagragian radii corresponding mass fractions
        rc: float
            Core radius
        mode: string
            sphere: calculate averaged properties from center to Lagrangian radii
            shell: calculate properties between two neighbor Lagrangian radii
        """    
        self.time = np.append(self.time, time)
        single_sim = SimpleParticle(single)
        single_sim.calcR2()
        binary_sim = SimpleParticle(binary)
        binary_sim.calcR2()
        all_sim = join(single_sim, binary_sim)
        n_single = single.size
        n_binary = binary.size

        idx = all_sim.r2.argsort()
        idx_single = idx[idx<n_single]
        idx_binary = idx[idx>=n_single] - n_single
        single_sort = single_sim[idx_single]
        binary_sort = binary_sim[idx_binary]
        all_sort = all_sim[idx]
    
        self.single.calcOneSnapshot(single_sort, rc, mode)
        self.binary.calcOneSnapshot(binary_sort, rc, mode)
        self.all.calcOneSnapshot(all_sort, rc, mode)
        if (self.binary.size != self.single.size):
            raise ValueError('Size inconsistence: single.size:', self.single.size, ' binary.size:', self.binary.size)

        self.size += 1
        
